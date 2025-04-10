import argparse
import logging
import socket
import sys
import threading
import time
import yaml
from datetime import datetime, timedelta

import numpy as np
import uhd

# === Fixed Measurement Parameters ===
CLOCK_TIMEOUT = 1000  # ms
INIT_DELAY = 0.2      # seconds
RATE = 250e3          # Hz
FREQ = 920e6          # Hz
CAPTURE_TIME = 2      # seconds

# Channel aliases
TX_A = 0
RX_A = 0
TX_B = 1
RX_B = 1

TX_CHANNELS = [TX_A, TX_B]
RX_CHANNELS = [RX_A, RX_B]

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

# Logging
class LogFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "[%(asctime)s] [%(levelname)s] %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: format,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(LogFormatter())
logger.addHandler(console)

def setup_clock(usrp):
    usrp.set_clock_source("external")
    logger.debug("Waiting for clock lock...")
    timeout = datetime.now() + timedelta(milliseconds=CLOCK_TIMEOUT)
    for i in range(usrp.get_num_mboards()):
        while not usrp.get_mboard_sensor("ref_locked", i) and datetime.now() < timeout:
            time.sleep(0.01)
        if not usrp.get_mboard_sensor("ref_locked", i):
            raise RuntimeError(f"Clock not locked on board {i}")
    logger.info("Clock locked.")

def setup_pps(usrp):
    usrp.set_time_source("external")
    usrp.set_time_unknown_pps(uhd.types.TimeSpec(0.0))
    logger.debug("PPS synced and device time set to 0")
    time.sleep(2)


def print_tune_result(tune_res):
    return (
        "Tune Result:\n    Target RF  Freq: {:.6f} (MHz)\n Actual RF  Freq: {:.6f} (MHz)\n Target DSP Freq: {:.6f} "
        "(MHz)\n "
        "Actual DSP Freq: {:.6f} (MHz)\n".format(
            (tune_res.target_rf_freq / 1e6),
            (tune_res.actual_rf_freq / 1e6),
            (tune_res.target_dsp_freq / 1e6),
            (tune_res.actual_dsp_freq / 1e6),
        )
    )
  
def tune_usrp(usrp, freq, channels, at_time):
    """Synchronously set the device's frequency."""
    treq = uhd.types.TuneRequest(freq)
    usrp.set_command_time(uhd.types.TimeSpec(at_time))
    treq.dsp_freq = 0.0
    treq.target_freq = freq
    treq.rf_freq = freq
    treq.rf_freq_policy = uhd.types.TuneRequestPolicy(ord("M"))
    treq.dsp_freq_policy = uhd.types.TuneRequestPolicy(ord("M"))
    args = uhd.types.DeviceAddr("mode_n=integer")
    treq.args = args
    rx_freq = freq - 1e3
    rreq = uhd.types.TuneRequest(rx_freq)
    rreq.rf_freq = rx_freq
    rreq.target_freq = rx_freq
    rreq.dsp_freq = 0.0
    rreq.rf_freq_policy = uhd.types.TuneRequestPolicy(ord("M"))
    rreq.dsp_freq_policy = uhd.types.TuneRequestPolicy(ord("M"))
    rreq.args = uhd.types.DeviceAddr("mode_n=fractional")
    for chan in channels:
        logger.debug(print_tune_result(usrp.set_rx_freq(rreq, chan)))
        logger.debug(print_tune_result(usrp.set_tx_freq(treq, chan)))
    while not usrp.get_rx_sensor("lo_locked").to_bool():
        print(".")
        time.sleep(0.01)
    logger.info("RX LO is locked")
    while not usrp.get_tx_sensor("lo_locked").to_bool():
        print(".")
        time.sleep(0.01)
    logger.info("TX LO is locked")

# Function to save metadata as YAML
def save_metadata_to_yaml(filename, metadata):
    with open(filename, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False)
    logger.info(f"Metadata saved to {filename}")
  
def setup(usrp, tx_gain_a, tx_gain_b, gain_db, exp_id, meas_id):
    usrp.set_master_clock_rate(20e6)
    setup_clock(usrp)
    setup_pps(usrp)
    channels = RX_CHANNELS

    metadata = {
        'experiment_id': exp_id,
        'measurement_id': meas_id,
        'tx_gain_a': tx_gain_a,
        'tx_gain_b': tx_gain_b,
        'rx_gain_a': gain_db[RX_A],
        'rx_gain_b': gain_db[RX_B],
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'sampling_rate': RATE,
        'frequency': FREQ,
        'capture_time': CAPTURE_TIME,
    }

    # Generate a unique filename for the metadata
    metadata_filename = f"metadata_{socket.gethostname()[4:]}_{exp_id}_{meas_id}_gainA{gain_db[RX_A]}_gainB{gain_db[RX_B]}_{TIMESTAMP}.yml"
    save_metadata_to_yaml(metadata_filename, metadata)

    # Set RX and TX parameters
    for ch in channels:
        usrp.set_rx_rate(RATE, ch)
        usrp.set_tx_rate(RATE, ch)
        usrp.set_rx_dc_offset(False, ch)  # DC offset correction disabled to preserve full dynamic range
        usrp.set_rx_bandwidth(200e3, ch)
        usrp.set_rx_agc(False, ch)
        usrp.set_rx_gain(gain_db[ch], ch)

    usrp.set_tx_gain(tx_gain_a, TX_A)
    usrp.set_tx_gain(tx_gain_b, TX_B)

    st_args = uhd.usrp.StreamArgs("fc32", "sc16")
    st_args.channels = channels
    tx_streamer = usrp.get_tx_stream(st_args)
    rx_streamer = usrp.get_rx_stream(st_args)

    usrp.set_time_unknown_pps(uhd.types.TimeSpec(0.0))
    logger.debug("[SYNC] Set time to 0.0 via PPS")
    time.sleep(2)
    tune_usrp(usrp, FREQ, channels, at_time=INIT_DELAY)
    return tx_streamer, rx_streamer

def tx_ref(usrp, tx_streamer, quit_event, phase, amplitude, start_time):
    global underrun_count, other_tx_errors
    underrun_count = 0
    other_tx_errors = 0
    num_channels = tx_streamer.get_num_channels()
    max_samps = tx_streamer.get_max_num_samps()
    amplitude = np.asarray(amplitude)
    phase = np.asarray(phase)
    sample = amplitude * np.exp(1j * phase)
    tx_buff = np.ones((num_channels, 1000 * max_samps), dtype=np.complex64)
    for ch in TX_CHANNELS:
        tx_buff[ch, :] *= sample[ch]
    tx_md = uhd.types.TXMetadata()
    tx_md.has_time_spec = True
    tx_md.time_spec = start_time

    logger.debug(f"TX scheduled at: {tx_md.time_spec.get_real_secs():.6f}, USRP time now: {usrp.get_time_now().get_real_secs():.6f}")

    try:
        first_tx = True
        async_metadata = uhd.types.TXAsyncMetadata()
        while not quit_event.is_set():
            if first_tx:
                logger.debug(f"TX send at USRP time: {usrp.get_time_now().get_real_secs():.6f}")
                first_tx = False
            tx_streamer.send(tx_buff, tx_md)
            if not tx_streamer.recv_async_msg(async_metadata, 0.1):
                continue

            # Handle the error codes
            if async_metadata.event_code == uhd.types.TXMetadataEventCode.burst_ack:
                return
            elif async_metadata.event_code in (
                uhd.types.TXMetadataEventCode.underflow,
                uhd.types.TXMetadataEventCode.underflow_in_packet,
            ):
                num_tx_underrun += 1
                logger.warning(f"TX underrun detected. Count: {num_tx_underrun}")
            elif async_metadata.event_code in (
                uhd.types.TXMetadataEventCode.seq_error,
                uhd.types.TXMetadataEventCode.seq_error_in_packet,
            ):
                num_tx_seqerr += 1
                logger.error(f"TX sequence error detected. Count: {num_tx_seqerr}")
            else:
                logger.warning(f"Unexpected event on async recv ({async_metadata.event_code}), continuing.")
    finally:
        tx_md.end_of_burst = True
        tx_streamer.send(np.zeros((num_channels, 0), dtype=np.complex64), tx_md)

def rx_ref(usrp, rx_streamer, quit_event, duration, result_container, start_time):
    timeout_errors = 0
    overflow_errors = 0
    other_errors = 0
    num_channels = rx_streamer.get_num_channels()
    max_samps = rx_streamer.get_max_num_samps()
    buffer_len = int(duration * RATE * 2)
    iq_data = np.empty((num_channels, buffer_len), dtype=np.complex64)
    rx_md = uhd.types.RXMetadata()
    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
    stream_cmd.stream_now = False
    stream_cmd.time_spec = start_time

    logger.debug(f"RX scheduled at: {stream_cmd.time_spec.get_real_secs():.6f}, USRP time now: {usrp.get_time_now().get_real_secs():.6f}")

    expected_start = stream_cmd.time_spec.get_real_secs()
    time_now = usrp.get_time_now().get_real_secs()
    timeout = (expected_start - time_now) + 1.0

    rx_streamer.issue_stream_cmd(stream_cmd)
    num_rx = 0
    try:
        first_iteration = True
        while not quit_event.is_set():
            recv_buff = np.zeros((num_channels, max_samps), dtype=np.complex64)
            n = rx_streamer.recv(recv_buff, rx_md, timeout)
            timeout = 1.0
            if rx_md.error_code == uhd.types.RXMetadataErrorCode.timeout:
                timeout_errors += 1
            elif rx_md.error_code == uhd.types.RXMetadataErrorCode.overflow:
                overflow_errors += 1
            elif rx_md.error_code != uhd.types.RXMetadataErrorCode.none:
                other_errors += 1
            if n > 0 and num_rx + n < buffer_len:
                iq_data[:, num_rx:num_rx+n] = recv_buff[:, :n]
                num_rx += n
    finally:
        rx_streamer.issue_stream_cmd(uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont))
        trimmed = iq_data[:, int(RATE // 10):num_rx]

        # Amplitude saturation check
        max_amplitude = np.max(np.abs(trimmed))
        if max_amplitude > 1.0:
            logger.warning(f"Potential IQ saturation: max amplitude = {max_amplitude:.4f} (> 1.0)")
        else:
            logger.debug(f"Max IQ amplitude: {max_amplitude:.4f}")

        # Quick indication: compute average phase difference
        phase_ch0 = np.unwrap(np.angle(trimmed[0]))
        phase_ch1 = np.unwrap(np.angle(trimmed[1]))
        phase_diff = phase_ch0 - phase_ch1
        avg_phase_diff_deg = np.rad2deg(np.angle(np.exp(1j * np.mean(phase_diff))))
        logger.info(f"Average phase difference CH0 - CH1: {avg_phase_diff_deg:.2f}°")
        phase_diff_std = np.rad2deg(np.std(phase_diff))
        logger.info(f"Phase difference std dev: {phase_diff_std:.2f}°")

        # Log IQ amplitude per channel
        for ch_idx, ch_label in zip([0, 1], ["A", "B"]):
            avg_amp = np.mean(np.abs(trimmed[ch_idx]))
            std_amp = np.std(np.abs(trimmed[ch_idx]))
            min_amp = np.min(np.abs(trimmed[ch_idx]))
            max_amp = np.max(np.abs(trimmed[ch_idx]))
            i_vals = np.real(trimmed[ch_idx])
            q_vals = np.imag(trimmed[ch_idx])
            max_i = np.max(np.abs(i_vals))
            max_q = np.max(np.abs(q_vals))
            logger.info(f"Amplitude RX {ch_label}: avg={avg_amp:.4f}, std={std_amp:.4f}, min={min_amp:.4f}, max={max_amp:.4f}")
            logger.info(f"RX {ch_label} max |I|: {max_i:.4f}, max |Q|: {max_q:.4f}")
            if max_i > 0.9 or max_q > 0.9:
                logger.warning(f"[RX {ch_label}] I/Q component close to saturation! Consider reducing gain.")
            if max_amp > 0.9:
                logger.warning(f"[RX {ch_label}] Amplitude close to saturation! Consider reducing gain.")

        logger.info(f"RX summary: timeouts={timeout_errors}, overflows={overflow_errors}, other errors={other_errors}")
        result_container.extend(trimmed)

def measure(usrp, tx_streamer, rx_streamer, tx_gain_a, tx_gain_b, gain_a, gain_b, exp_id, meas_id):
    usrp.set_rx_gain(gain_a, RX_A)
    usrp.set_rx_gain(gain_b, RX_B)

    
    filename = f"data_{socket.gethostname()[4:]}_{exp_id}_{meas_id}_gainA{gain_a}_gainB{gain_b}_{TIMESTAMP}.npy"
    quit_event_rx = threading.Event()
    quit_event_tx = threading.Event()
    results = []


    now = usrp.get_time_now().get_real_secs()
    start_time_tx = uhd.types.TimeSpec(now + 1.0)
    start_time_rx = uhd.types.TimeSpec(now + 2.0)
    logger.debug("Scheduled TX start_time: {:.6f} MHz, RX start_time: {:.6f} MHz, USRP time now: {:.6f}".format(
        start_time_tx.get_real_secs(), start_time_rx.get_real_secs(), now))

    rx_thr = threading.Thread(target=rx_ref, args=(usrp, rx_streamer, quit_event_rx, CAPTURE_TIME, results, start_time_rx))
    tx_thr = threading.Thread(target=tx_ref, args=(usrp, tx_streamer, quit_event_tx, [0.0, 0.0], [0.8, 0.8], start_time_tx))


    tx_thr.start()
    rx_thr.start()
   


    rx_start_real = start_time_rx.get_real_secs()
    now = usrp.get_time_now().get_real_secs()
    sleep_duration = max(CAPTURE_TIME, rx_start_real - now + CAPTURE_TIME)
    time.sleep(sleep_duration)
    quit_event_rx.set()
    rx_thr.join()
    quit_event_tx.set()
    tx_thr.join()
    logger.info(f"TX summary: underruns={underrun_count}, other TX errors={other_tx_errors}")

    np.save(filename, results)
    logger.info(f"Saved IQ data to {filename}")

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp", type=str, required=True, help="Experiment ID")
    parser.add_argument("--meas", type=int, required=True, help="Measurement ID")
    parser.add_argument("--tx_gain_a", type=float, required=True, help="TX gain for channel A")
    parser.add_argument("--tx_gain_b", type=float, required=True, help="TX gain for channel B")
    parser.add_argument("--gain_a", type=int, required=True, help="Fixed RX gain for Board A (CH0)")
    parser.add_argument("--gain_b", type=int, required=True, help="RX gain for Board B (CH1)")
    return parser.parse_args()

def main():
    args = parse_arguments()
    usrp = uhd.usrp.MultiUSRP("type=b200")
    tx_streamer, rx_streamer = setup(usrp, args.tx_gain_a, args.tx_gain_b, {RX_A: args.gain_a, RX_B: args.gain_b}, args.exp, args.meas)
    measure(usrp, tx_streamer, rx_streamer, args.tx_gain_a, args.tx_gain_b, args.gain_a, args.gain_b, args.exp, args.meas)

if __name__ == "__main__":
    main()
