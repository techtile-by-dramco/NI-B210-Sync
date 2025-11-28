import logging
import os
import socket
import sys
import threading
import time
from datetime import datetime, timedelta
import numpy as np
import uhd
import yaml
import tools
import argparse
import zmq
import queue

# =============================================================================
#                           Experiment Configuration
# =============================================================================
# This section defines the default settings and timing parameters
# used throughout the measurement and loopback procedure.
# Values can be overridden by entries in the configuration YAML file.
# =============================================================================

CMD_DELAY = 0.05          # Command delay (50 ms) between USRP instructions
RX_TX_SAME_CHANNEL = True # True if loopback occurs between the same RF channel
CLOCK_TIMEOUT = 1000      # Timeout for external clock locking (in ms)
INIT_DELAY = 0.2          # Initial delay before starting transmission (200 ms)
RATE = 250e3              # Sampling rate in samples per second (250 kSps)
LOOPBACK_TX_GAIN = 50 #70     # Empirically determined transmit gain for loopback tests
RX_GAIN = 22              # Empirically determined receive gain (22 dB without splitter, 27 dB with splitter)
CAPTURE_TIME = 10         # Duration of each capture in seconds
FREQ = 0                  # Base frequency offset (Hz); 0 means use default center frequency
# server_ip = "10.128.52.53"  # Optional remote server address (commented out)
meas_id = 0               # Measurement identifier
exp_id = 0                # Experiment identifier
# =============================================================================
# =============================================================================

results = []

SWITCH_LOOPBACK_MODE = 0x00000006 # which is 110
SWITCH_RESET_MODE = 0x00000000

context = zmq.Context()

iq_socket = context.socket(zmq.PUB)

iq_socket.bind(f"tcp://*:{50001}")

HOSTNAME = socket.gethostname()[4:]
file_open = False
server_ip = None  # populated by settings.yml

# =============================================================================
#                           Custom Log Formatter
# =============================================================================
# This formatter adds timestamps with fractional seconds to log messages,
# allowing for more precise event timing (useful in measurement systems).
# =============================================================================

class LogFormatter(logging.Formatter):
    """Custom log formatter that prints timestamps with fractional seconds."""

    @staticmethod
    def pp_now():
        """Return the current time of day as a formatted string with milliseconds."""
        now = datetime.now()
        return "{:%H:%M}:{:05.2f}".format(now, now.second + now.microsecond / 1e6)

    def formatTime(self, record, datefmt=None):
        """Override the default time formatter to include fractional seconds."""
        converter = self.converter(record.created)
        if datefmt:
            formatted_date = converter.strftime(datefmt)
        else:
            formatted_date = LogFormatter.pp_now()
        return formatted_date

# =============================================================================
#                           Logger and Channel Configuration
# =============================================================================
# This section initializes the global logger and defines the
# channel mapping used for reference and loopback measurements.
# =============================================================================

global logger
global begin_time

connected_to_server = False
begin_time = 2.0

# -------------------------------------------------------------------------
# Logger setup
# -------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Stream logs to console
console = logging.StreamHandler()
logger.addHandler(console)

# Custom log format (includes time, level, and thread name)
formatter = LogFormatter(
    fmt="[%(asctime)s] [%(levelname)s] (%(threadName)-10s) %(message)s"
)
console.setFormatter(formatter)

# -------------------------------------------------------------------------
# Topic identifiers for ZMQ or internal messaging
# -------------------------------------------------------------------------
TOPIC_CH0 = b"CH0"
TOPIC_CH1 = b"CH1"

# -------------------------------------------------------------------------
# Channel configuration depending on whether RX and TX share the same channel
# -------------------------------------------------------------------------
if RX_TX_SAME_CHANNEL:
    # Reference signal received on CH0, loopback on CH1
    REF_RX_CH = FREE_TX_CH = 0
    LOOPBACK_RX_CH = LOOPBACK_TX_CH = 1
    logger.debug("\nPLL REF → CH0 RX\nCH1 TX → CH1 RX\nCH0 TX →")
else:
    # Reference and loopback channels are swapped
    LOOPBACK_RX_CH = FREE_TX_CH = 0
    REF_RX_CH = LOOPBACK_TX_CH = 1
    logger.debug("\nPLL REF → CH1 RX\nCH1 TX → CH0 RX\nCH0 TX →")
# =============================================================================
# =============================================================================


def rx_ref(usrp, rx_streamer, quit_event, duration, result_queue, start_time=None):
    # https://files.ettus.com/manual/page_sync.html#sync_phase_cordics
    # The CORDICs are reset at each start-of-burst command, so users should ensure that every start-of-burst also has a time spec set.
    logger.debug(f"GAIN IS CH0: {usrp.get_rx_gain(0)} CH1: {usrp.get_rx_gain(1)}")

    global results
    num_channels = rx_streamer.get_num_channels()
    max_samps_per_packet = rx_streamer.get_max_num_samps()
    buffer_length = int(duration * RATE * 2)
    iq_data = np.empty((num_channels, buffer_length), dtype=np.complex64)

    recv_buffer = np.zeros((num_channels, max_samps_per_packet), dtype=np.complex64)
    rx_md = uhd.types.RXMetadata()
    # Craft and send the Stream Command
    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
    # The stream now parameter controls when the stream begins. When true, the device will begin streaming ASAP. When false, the device will begin streaming at a time specified by time_spec.
    stream_cmd.stream_now = False
    timeout = 1.0
    if start_time is not None:
        stream_cmd.time_spec = start_time
        time_diff = start_time.get_real_secs() - usrp.get_time_now().get_real_secs()
        if time_diff > 0:
            timeout = 1.0 + time_diff
    else:
        stream_cmd.time_spec = uhd.types.TimeSpec(
            usrp.get_time_now().get_real_secs() + INIT_DELAY + 0.1
        )
    rx_streamer.issue_stream_cmd(stream_cmd)
    try:
        num_rx = 0
        while not quit_event.is_set():
            try:
                num_rx_i = rx_streamer.recv(recv_buffer, rx_md, timeout)
                if rx_md.error_code != uhd.types.RXMetadataErrorCode.none:
                    logger.error(rx_md.error_code)
                else:
                    if num_rx_i > 0:
                        # samples = recv_buffer[:,:num_rx_i]
                        # send_rx(samples)
                        samples = recv_buffer[:, :num_rx_i]
                        if num_rx + num_rx_i > buffer_length:
                            logger.error(
                                "more samples received than buffer long, not storing the data"
                            )
                        else:
                            iq_data[:, num_rx : num_rx + num_rx_i] = samples
                            # threading.Thread(target=send_rx,
                            #                  args=(samples,)).start()
                            num_rx += num_rx_i
            except RuntimeError as ex:
                logger.error("Runtime error in receive: %s", ex)
                return
    except KeyboardInterrupt:
        pass
    finally:
        logger.debug("CTRL+C is pressed or duration is reached, closing off ")
        rx_streamer.issue_stream_cmd(
            uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
        )
        iq_samples = iq_data[:, int(RATE // 10) : num_rx]

        np.save(file_name_state, iq_samples)

        phase_ch0, freq_slope_ch0 = tools.get_phases_and_apply_bandpass(iq_samples[0, :])
        phase_ch1, freq_slope_ch1 = tools.get_phases_and_apply_bandpass(iq_samples[1, :])

        logger.debug("Frequency offset CH0: %.4f", freq_slope_ch0 / (2 * np.pi))
        logger.debug("Frequency offset CH1: %.4f", freq_slope_ch1 / (2 * np.pi))

        logger.debug("Phase offset CH0: %.4f", np.rad2deg(phase_ch0).mean())
        logger.debug("Phase offset CH1: %.4f", np.rad2deg(phase_ch1).mean())

        phase_diff = tools.to_min_pi_plus_pi(phase_ch0 - phase_ch1, deg=False)

        # phase_diff = phase_ch0 - phase_ch1

        _circ_mean = tools.circmean(phase_diff, deg=False)
        _mean = np.mean(phase_diff)

        logger.debug("Diff cirmean and mean: %.6f", _circ_mean - _mean)

        result_queue.put(_mean)

        avg_ampl = np.mean(np.abs(iq_samples), axis=1)
        # var_ampl = np.var(np.abs(iq_samples), axis=1)

        max_I = np.max(np.abs(np.real(iq_samples)), axis=1)
        max_Q = np.max(np.abs(np.imag(iq_samples)), axis=1)

        logger.debug(
            "MAX AMPL IQ CH0: I %.6f Q %.6f CH1:I %.6f Q %.6f",
            max_I[0],
            max_Q[0],
            max_I[1],
            max_Q[1],
        )

        logger.debug(
            "AVG AMPL IQ CH0: %.6f CH1: %.6f",
            avg_ampl[0],
            avg_ampl[1],
        )


def setup_clock(usrp, clock_src, num_mboards):
    usrp.set_clock_source(clock_src)
    logger.debug("Now confirming lock on clock signals...")
    end_time = datetime.now() + timedelta(milliseconds=CLOCK_TIMEOUT)
    # Lock onto clock signals for all mboards
    for i in range(num_mboards):
        is_locked = usrp.get_mboard_sensor("ref_locked", i)
        while (not is_locked) and (datetime.now() < end_time):
            time.sleep(1e-3)
            is_locked = usrp.get_mboard_sensor("ref_locked", i)
        if not is_locked:
            logger.error("Unable to confirm clock signal locked on board %d", i)
            return False
        else:
            logger.debug("Clock signals are locked")
    return True


def setup_pps(usrp, pps):
    """Setup the PPS source"""

    logger.debug("Setting PPS")
    usrp.set_time_source(pps)
    return True


def print_tune_result(tune_res):
    logger.debug(
        "Tune Result:\n    Target RF  Freq: %.6f (MHz)\n Actual RF  Freq: %.6f (MHz)\n Target DSP Freq: %.6f "
        "(MHz)\n "
        "Actual DSP Freq: %.6f (MHz)\n",
        (tune_res.target_rf_freq / 1e6),
        (tune_res.actual_rf_freq / 1e6),
        (tune_res.target_dsp_freq / 1e6),
        (tune_res.actual_dsp_freq / 1e6),
    )


def tune_usrp(usrp, freq, channels, at_time):
    """Synchronously set the device's frequency.
    If a channel is using an internal LO it will be tuned first
    and every other channel will be manually tuned based on the response.
    This is to account for the internal LO channel having an offset in the actual DSP frequency.
    Then all channels are synchronously tuned."""
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
        print_tune_result(usrp.set_rx_freq(rreq, chan))
        print_tune_result(usrp.set_tx_freq(treq, chan))
    while not usrp.get_rx_sensor("lo_locked").to_bool():
        print(".")
        time.sleep(0.01)
    logger.info("RX LO is locked")
    while not usrp.get_tx_sensor("lo_locked").to_bool():
        print(".")
        time.sleep(0.01)
    logger.info("TX LO is locked")


def wait_till_go_from_server(ip, _connect=True):

    global meas_id, file_open, data_file, file_name
    # Connect to the publisher's address
    logger.debug("Connecting to server %s.", ip)
    sync_socket = context.socket(zmq.SUB)

    alive_socket = context.socket(zmq.REQ)

    sync_socket.connect(f"tcp://{ip}:{5557}")
    alive_socket.connect(f"tcp://{ip}:{5558}")
    # Subscribe to topics
    sync_socket.subscribe("")

    logger.debug("Sending ALIVE")
    alive_socket.send_string(HOSTNAME)
    # Receives a string format message
    logger.debug("Waiting on SYNC from server %s.", ip)

    meas_id, unique_id = sync_socket.recv_string().split(" ")

    file_name = f"data_{HOSTNAME}_{unique_id}_{meas_id}"

    if not file_open:
        data_file = open(f"data_{HOSTNAME}_{unique_id}.txt", "a")
        file_open = True

    logger.debug(meas_id)

    alive_socket.close()
    sync_socket.close()

def send_usrp_in_tx_mode(ip):
    tx_mode_socket = context.socket(zmq.REQ)
    tx_mode_socket.connect(f"tcp://{ip}:{5559}")
    logger.debug("USRP IN TX MODE")
    tx_mode_socket.send_string(HOSTNAME)
    tx_mode_socket.close()


def setup(usrp, server_ip, connect=True):
    rate = RATE
    mcr = 20e6
    assert (
        mcr / rate
    ).is_integer(), f"The masterclock rate {mcr} should be an integer multiple of the sampling rate {rate}"
    # Manual selection of master clock rate may also be required to synchronize multiple B200 units in time.
    usrp.set_master_clock_rate(mcr)
    channels = [0, 1]
    setup_clock(usrp, "external", usrp.get_num_mboards())
    setup_pps(usrp, "external")
    # smallest as possible (https://files.ettus.com/manual/page_usrp_b200.html#b200_fe_bw)
    rx_bw = 200e3
    for chan in channels:
        usrp.set_rx_rate(rate, chan)
        usrp.set_tx_rate(rate, chan)
        # NOTE DC offset is enabled
        usrp.set_rx_dc_offset(True, chan)
        usrp.set_rx_bandwidth(rx_bw, chan)
        usrp.set_rx_agc(False, chan)
    # specific settings from loopback/REF PLL
    usrp.set_tx_gain(LOOPBACK_TX_GAIN, LOOPBACK_TX_CH)
    usrp.set_tx_gain(LOOPBACK_TX_GAIN, FREE_TX_CH)

    usrp.set_rx_gain(LOOPBACK_RX_GAIN, LOOPBACK_RX_CH)
    usrp.set_rx_gain(REF_RX_GAIN, REF_RX_CH)
    # streaming arguments
    st_args = uhd.usrp.StreamArgs("fc32", "sc16")
    st_args.channels = channels
    # streamers
    tx_streamer = usrp.get_tx_stream(st_args)
    rx_streamer = usrp.get_rx_stream(st_args)
    # Step1: wait for the last pps time to transition to catch the edge
    # Step2: set the time at the next pps (synchronous for all boards)
    # this is better than set_time_next_pps as we wait till the next PPS to transition and after that we set the time.
    # this ensures that the FPGA has enough time to clock in the new timespec (otherwise it could be too close to a PPS edge)
    wait_till_go_from_server(server_ip, connect)
    logger.info("Setting device timestamp to 0...")
    usrp.set_time_unknown_pps(uhd.types.TimeSpec(0.0))

    usrp.set_time_unknown_pps(uhd.types.TimeSpec(0.0))
    logger.debug("[SYNC] Resetting time.")
    logger.info(f"RX GAIN PROFILE CH0: {usrp.get_rx_gain_names(0)}")
    logger.info(f"RX GAIN PROFILE CH1: {usrp.get_rx_gain_names(1)}")
    # we wait 2 seconds to ensure a PPS rising edge occurs and latches the 0.000s value to both USRPs.
    time.sleep(2)
    tune_usrp(usrp, FREQ, channels, at_time=begin_time)
    logger.info(
        f"USRP has been tuned and setup. ({usrp.get_time_now().get_real_secs()})"
    )
    return tx_streamer, rx_streamer


def rx_thread(usrp, rx_streamer, quit_event, duration, res, start_time=None):
    _rx_thread = threading.Thread(
        target=rx_ref,
        args=(
            usrp,
            rx_streamer,
            quit_event,
            duration,
            res,
            start_time,
        ),
    )
    _rx_thread.name = "RX_thread"
    _rx_thread.start()
    return _rx_thread


def tx_async_th(tx_streamer, quit_event):
    async_metadata = uhd.types.TXAsyncMetadata()
    try:
        while not quit_event.is_set():
            if not tx_streamer.recv_async_msg(async_metadata, 0.01):
                continue
            else:
                if async_metadata.event_code != uhd.types.TXMetadataEventCode.burst_ack:
                    logger.error(async_metadata.event_code)
    except KeyboardInterrupt:
        pass


def delta(usrp, at_time):
    return at_time - usrp.get_time_now().get_real_secs()


def get_current_time(usrp):
    return usrp.get_time_now().get_real_secs()


def tx_thread(
    usrp, tx_streamer, quit_event, phase=[0, 0], amplitude=[0.8, 0.8], start_time=None
):
    tx_thr = threading.Thread(
        target=tx_ref,
        args=(usrp, tx_streamer, quit_event, phase, amplitude, start_time),
    )

    tx_thr.name = "TX_thread"
    tx_thr.start()

    return tx_thr


def tx_ref(usrp, tx_streamer, quit_event, phase, amplitude, start_time=None):
    """
    Transmit a continuous reference signal on all active channels.

    This function generates a complex baseband signal based on the provided
    amplitude and phase values, then continuously transmits it using the
    specified USRP transmit streamer until `quit_event` is set.

    Args:
        usrp: The USRP device instance.
        tx_streamer: UHD transmit streamer used for sending samples.
        quit_event: Threading event used to stop transmission when set.
        phase (list or np.ndarray): Phase offset for each channel (in radians).
        amplitude (list or np.ndarray): Amplitude for each channel.
        start_time (uhd.types.TimeSpec, optional): Scheduled start time.
            If None, transmission begins after `INIT_DELAY` seconds.

    Notes:
        - This function continuously sends the same buffer of complex samples.
        - It is typically used to generate a reference signal for phase calibration.
    """

    # Retrieve USRP transmission parameters
    num_channels = tx_streamer.get_num_channels()
    max_samps_per_packet = tx_streamer.get_max_num_samps()

    # Convert inputs to NumPy arrays for element-wise operations
    amplitude = np.asarray(amplitude)
    phase = np.asarray(phase)

    # Compute the complex signal for each channel: A * e^(j * phi)
    sample = amplitude * np.exp(1j * phase)

    # Initialize a large transmit buffer filled with the reference signal
    transmit_buffer = np.ones(
        (num_channels, 1000 * max_samps_per_packet), dtype=np.complex64
    )
    transmit_buffer[0, :] *= sample[0]
    transmit_buffer[1, :] *= sample[1]

    # Create UHD transmit metadata (for timed transmission)
    tx_md = uhd.types.TXMetadata()

    # Schedule the transmission start time
    if start_time is not None:
        tx_md.time_spec = start_time
    else:
        tx_md.time_spec = uhd.types.TimeSpec(
            usrp.get_time_now().get_real_secs() + INIT_DELAY
        )

    tx_md.has_time_spec = True

    try:
        # Continuously transmit the reference signal until quit_event is triggered
        while not quit_event.is_set():
            tx_streamer.send(transmit_buffer, tx_md)

    except KeyboardInterrupt:
        logger.debug("CTRL+C detected — stopping transmission")

    finally:
        # Send an end-of-burst (EOB) packet to properly terminate streaming
        tx_md.end_of_burst = True
        tx_streamer.send(np.zeros((num_channels, 0), dtype=np.complex64), tx_md)


def tx_meta_thread(tx_streamer, quit_event):
    tx_meta_thr = threading.Thread(target=tx_async_th, args=(tx_streamer, quit_event))

    tx_meta_thr.name = "TX_META_thread"
    tx_meta_thr.start()
    return tx_meta_thr


def starting_in(usrp, at_time):
    return f"Starting in {delta(usrp, at_time):.2f}s"


def measure_pilot(usrp, tx_streamer, rx_streamer, quit_event, result_queue, at_time=None):
    """
    Perform a pilot measurement using the specified USRP device and RX streamer.

    This function:
    - Configures the RX antenna for pilot capture
    - Starts a receive thread to record samples
    - Waits until the capture is complete
    - Restores the default antenna configuration

    Parameters
    ----------
    usrp : uhd.usrp.MultiUSRP
        The USRP device instance.
    rx_streamer : uhd.usrp.RXStreamer
        The receive streamer for data capture.
    quit_event : threading.Event
        Event object to control and stop the RX thread.
    result_queue : queue.Queue
        Queue used to store measurement results (e.g., captured phase).
    at_time : float, optional
        Scheduled start time for the measurement (in seconds).
    """
    logger.debug("########### Measure PILOT ###########")

    # # ------------------------------------------------------------
    # # 1. Configure transmit signal amplitudes
    # # ------------------------------------------------------------
    # amplitudes = [0.0, 0.0]              # Initialize amplitude array for both channels
    # amplitudes[LOOPBACK_TX_CH] = 0.8     # Enable TX on the selected loopback channel

    # # Define start time for the measurement
    # start_time = uhd.types.TimeSpec(at_time)
    # logger.debug(starting_in(usrp, at_time))


    # user_settings = None
    # try:
    #     user_settings = usrp.get_user_settings_iface(1)
    #     if user_settings:
    #         # Read current register value (for debug)
    #         logger.debug(user_settings.peek32(0))
    #         # Write a value to activate loopback mode
    #         user_settings.poke32(0, SWITCH_LOOPBACK_MODE)
    #         # Read again to verify the register value was updated
    #         logger.debug(user_settings.peek32(0))
    #     else:
    #         logger.error("Cannot write to user settings.")
    # except Exception as e:
    #     logger.error(e)

    
    # tx_thr = tx_thread(
    #     usrp,
    #     tx_streamer,
    #     quit_event,
    #     amplitude=amplitudes,
    #     phase=[0.0, 0.0],
    #     start_time=start_time,
    # )

    
    # # Thread responsible for handling TX metadata (timestamps, etc.)
    # tx_meta_thr = tx_meta_thread(tx_streamer, quit_event)

    


    # # Start RX thread for data acquisition
    # rx_thr = rx_thread(
    #     usrp=usrp,
    #     rx_streamer=rx_streamer,
    #     quit_event=quit_event,
    #     duration=CAPTURE_TIME,
    #     res=result_queue,
    #     start_time=start_time,
    # )

    # # Wait until capture completes (capture time + device delay)
    # time.sleep(CAPTURE_TIME + delta(usrp, at_time))

    # # Stop RX thread and wait for it to terminate
    # quit_event.set()

    # tx_thr.join()
    # rx_thr.join()

    # tx_meta_thr.join()

    # # ------------------------------------------------------------
    # # 7. Reset the RF switch control (disable loopback mode)
    # # ------------------------------------------------------------
    # if user_settings:
    #     user_settings.poke32(0, SWITCH_RESET_MODE)

    # # Clear event for next use
    # quit_event.clear()


   # ------------------------------------------------------------
    # 1. Configure transmit signal amplitudes
    # ------------------------------------------------------------
    amplitudes = [0.0, 0.0]              # Initialize amplitude array for both channels
    amplitudes[LOOPBACK_TX_CH] = 0.8     # Enable TX on the selected loopback channel

    # ------------------------------------------------------------
    # 2. Set the transmission start time
    # ------------------------------------------------------------
    start_time = uhd.types.TimeSpec(at_time)
    logger.debug(starting_in(usrp, at_time))

    # ------------------------------------------------------------
    # 3. (Legacy) Access user settings interface for low-level FPGA control
    #    Used to switch the USRP into "loopback mode" by writing to
    #    a register in the user settings interface.
    #    NOTE: This interface is no longer available in UHD 4.x.
    # ------------------------------------------------------------
    user_settings = None
    try:
        user_settings = usrp.get_user_settings_iface(1)
        if user_settings:
            # Read current register value (for debug)
            logger.debug(user_settings.peek32(0))
            # Write a value to activate loopback mode
            user_settings.poke32(0, SWITCH_LOOPBACK_MODE)
            # Read again to verify the register value was updated
            logger.debug(user_settings.peek32(0))
        else:
            logger.error("Cannot write to user settings.")
    except Exception as e:
        logger.error(e)

    # ------------------------------------------------------------
    # 4. Start transmit (TX), metadata, and receive (RX) threads
    # ------------------------------------------------------------
    tx_thr = tx_thread(
        usrp,
        tx_streamer,
        quit_event,
        amplitude=amplitudes,
        phase=[0.0, 0.0],
        start_time=start_time,
    )

    # Thread responsible for handling TX metadata (timestamps, etc.)
    tx_meta_thr = tx_meta_thread(tx_streamer, quit_event)

    # Thread that captures received samples during loopback
    rx_thr = rx_thread(
        usrp,
        rx_streamer,
        quit_event,
        duration=CAPTURE_TIME,
        res=result_queue,
        start_time=start_time,
    )

    # ------------------------------------------------------------
    # 5. Wait for the capture duration plus some safety margin (delta)
    # ------------------------------------------------------------
    time.sleep(CAPTURE_TIME + delta(usrp, at_time))

    # ------------------------------------------------------------
    # 6. Signal all threads to stop and wait for them to finish
    # ------------------------------------------------------------
    quit_event.set()   # Triggers thread termination
    tx_thr.join()
    rx_thr.join()
    tx_meta_thr.join()

    # ------------------------------------------------------------
    # 7. Reset the RF switch control (disable loopback mode)
    # ------------------------------------------------------------
    if user_settings:
        user_settings.poke32(0, SWITCH_RESET_MODE)

    # ------------------------------------------------------------
    # 8. Clear the quit event flag to prepare for the next measurement
    # ------------------------------------------------------------
    quit_event.clear()


def measure_loopback(
    usrp, tx_streamer, rx_streamer, quit_event, result_queue, at_time=None
):
    # ------------------------------------------------------------
    # Function: measure_loopback
    # Purpose:
    #   This function performs a loopback measurement using a USRP device.
    #   It transmits a known signal on one channel and simultaneously
    #   receives it on another channel (loopback). The result is captured,
    #   stored, and processed later.
    # ------------------------------------------------------------

    logger.debug("########### Measure LOOPBACK ###########")

    # ------------------------------------------------------------
    # 1. Configure transmit signal amplitudes
    # ------------------------------------------------------------
    amplitudes = [0.0, 0.0]              # Initialize amplitude array for both channels
    amplitudes[LOOPBACK_TX_CH] = 0.8     # Enable TX on the selected loopback channel

    # ------------------------------------------------------------
    # 2. Set the transmission start time
    # ------------------------------------------------------------
    start_time = uhd.types.TimeSpec(at_time)
    logger.debug(starting_in(usrp, at_time))

    # ------------------------------------------------------------
    # 3. (Legacy) Access user settings interface for low-level FPGA control
    #    Used to switch the USRP into "loopback mode" by writing to
    #    a register in the user settings interface.
    #    NOTE: This interface is no longer available in UHD 4.x.
    # ------------------------------------------------------------
    user_settings = None
    try:
        user_settings = usrp.get_user_settings_iface(1)
        if user_settings:
            # Read current register value (for debug)
            logger.debug(user_settings.peek32(0))
            # Write a value to activate loopback mode
            user_settings.poke32(0, SWITCH_LOOPBACK_MODE)
            # Read again to verify the register value was updated
            logger.debug(user_settings.peek32(0))
        else:
            logger.error("Cannot write to user settings.")
    except Exception as e:
        logger.error(e)

    # ------------------------------------------------------------
    # 4. Start transmit (TX), metadata, and receive (RX) threads
    # ------------------------------------------------------------
    tx_thr = tx_thread(
        usrp,
        tx_streamer,
        quit_event,
        amplitude=amplitudes,
        phase=[0.0, 0.0],
        start_time=start_time,
    )

    # Thread responsible for handling TX metadata (timestamps, etc.)
    tx_meta_thr = tx_meta_thread(tx_streamer, quit_event)

    # Thread that captures received samples during loopback
    rx_thr = rx_thread(
        usrp,
        rx_streamer,
        quit_event,
        duration=CAPTURE_TIME,
        res=result_queue,
        start_time=start_time,
    )

    # ------------------------------------------------------------
    # 5. Wait for the capture duration plus some safety margin (delta)
    # ------------------------------------------------------------
    time.sleep(CAPTURE_TIME + delta(usrp, at_time))

    # ------------------------------------------------------------
    # 6. Signal all threads to stop and wait for them to finish
    # ------------------------------------------------------------
    quit_event.set()   # Triggers thread termination
    tx_thr.join()
    rx_thr.join()
    tx_meta_thr.join()

    # ------------------------------------------------------------
    # 7. Reset the RF switch control (disable loopback mode)
    # ------------------------------------------------------------
    if user_settings:
        user_settings.poke32(0, SWITCH_RESET_MODE)

    # ------------------------------------------------------------
    # 8. Clear the quit event flag to prepare for the next measurement
    # ------------------------------------------------------------
    quit_event.clear()



def tx_phase_coh(usrp, tx_streamer, quit_event, phase_corr, at_time, long_time=True):
    """
    Transmit a coherent signal with an adjusted phase correction.

    This function starts a transmission thread that sends a signal with
    a specific phase correction on the loopback transmit channel.
    It also launches a metadata thread to handle UHD transmission metadata.
    The function blocks until the transmission time has elapsed, then stops
    both threads cleanly.

    Args:
        usrp: The USRP device instance.
        tx_streamer: UHD transmit streamer.
        quit_event: Threading event to signal thread termination.
        phase_corr (float): Phase correction value (in radians).
        at_time (float): Scheduled start time for transmission.
        long_time (bool): If True, use TX_TIME; otherwise, transmit for 10 seconds.
    """
    logger.debug("########### TX with adjusted phases ###########")

    # Initialize arrays for phase and amplitude per TX channel
    phases = [0.0, 0.0]
    amplitudes = [0.0, 0.0]

    # Apply phase correction and amplitude to the loopback transmit channel
    phases[LOOPBACK_TX_CH] = phase_corr
    amplitudes[LOOPBACK_TX_CH] = 0.8

    logger.debug(f"Phases: {phases}")
    logger.debug(f"amplitudes: {amplitudes}")
    logger.debug(f"TX Gain: {FREE_TX_GAIN}")

    # Set the transmit gain for the active channel
    usrp.set_tx_gain(FREE_TX_GAIN, LOOPBACK_TX_CH)

    # Define the UHD transmission start time
    start_time = uhd.types.TimeSpec(at_time)

    # Start the transmit thread
    tx_thr = tx_thread(
        usrp,
        tx_streamer,
        quit_event,
        amplitude=amplitudes,
        phase=phases,
        start_time=start_time,
    )

    # Start the metadata monitoring thread
    tx_meta_thr = tx_meta_thread(tx_streamer, quit_event)

    # Send USRP is in TX mode for scope measurements
    send_usrp_in_tx_mode(server_ip)

    # Allow transmission to continue for the configured duration
    if long_time:
        time.sleep(TX_TIME + delta(usrp, at_time))
    else:
        time.sleep(10.0 + delta(usrp, at_time))

    # Signal all threads to stop
    quit_event.set()

    # Ensure both threads terminate cleanly
    tx_thr.join()
    tx_meta_thr.join()

    logger.debug("Transmission completed successfully")

    return tx_thr, tx_meta_thr


def parse_arguments():
    """
    Parse command-line arguments for the beamforming (BF) application.

    This function checks for the optional server IP argument (-i or --ip)
    and updates the global variable `server_ip` if provided.

    Example:
        python script.py -i 192.168.1.10
    """
    global server_ip

    # Create an argument parser with a brief description
    parser = argparse.ArgumentParser(description="Beamforming control script")

    # Optional argument for specifying the server IP
    parser.add_argument(
        "-i",
        "--ip",
        type=str,
        help="IP address of the server (optional)",
        required=False,
    )

    # Parse the command-line arguments
    args = parser.parse_args()

    # If the user provided an IP address, apply it
    if args.ip:
        logger.debug(f"Setting server IP to: {args.ip}")
        server_ip = args.ip


def main():
    global meas_id, file_name_state

    parse_arguments()

    try:
        # Attempt to open and load calibration settings from the YAML file
        with open(os.path.join(os.path.dirname(__file__), "cal-settings.yml"), "r") as file:
            vars = yaml.safe_load(file)
            globals().update(vars)  # update the global variables with the vars in yaml
    except FileNotFoundError:
        logger.error("Calibration file 'cal-settings.yml' not found in the current directory.")
        exit()
    except yaml.YAMLError as e:
        logger.error(f"Error parsing 'cal-settings.yml': {e}")
        exit()
    except Exception as e:
        logger.error(f"Unexpected error while loading calibration settings: {e}")
        exit()

    try:
        # Get current path
        script_dir = os.path.dirname(os.path.realpath(__file__))

        # FPGA file path
        fpga_path = os.path.join(script_dir, "usrp_b210_fpga_loopback.bin")

        # Initialize USRP device with custom FPGA image and integer mode
        usrp = uhd.usrp.MultiUSRP(
            "enable_user_regs, " \
            f"fpga={fpga_path}, " \
            "mode_n=integer"
        )
        logger.info("Using Device: %s", usrp.get_pp_string())

        # -------------------------------------------------------------------------
        # STEP 0: Preparations
        # -------------------------------------------------------------------------

        # Set up TX and RX streamers and establish connection
        tx_streamer, rx_streamer = setup(usrp, server_ip, connect=True)

        # Event used to control thread termination
        quit_event = threading.Event()

        margin = 5.0                     # Safety margin for timing
        cmd_time = CAPTURE_TIME + margin # Duration for one measurement step
        start_next_cmd = cmd_time        # Timestamp for the next scheduled command

        # Queue to collect measurement results and communicate between threads
        result_queue = queue.Queue()

        # -------------------------------------------------------------------------
        # STEP 1: Perform loopback measurement with reference signal
        # -------------------------------------------------------------------------

        # # --- Perform pilot measurement ---
        # file_name_state = file_name + "_pilot"
        # measure_pilot(
        #     usrp,
        #     tx_streamer,
        #     rx_streamer,
        #     quit_event,
        #     result_queue,
        #     at_time=start_next_cmd
        # )

        # # Retrieve pilot phase result
        # phi_P = result_queue.get()

        # # Print pilot phase
        # logger.info("Phase pilot reference signal: %s", phi_P)

        start_next_cmd += cmd_time + 1.0  # Schedule next command after delay

        # -------------------------------------------------------------------------
        # STEP 2: Perform internal loopback measurement with reference signal
        # -------------------------------------------------------------------------

        file_name_state = file_name + "_loopback"
        measure_loopback(
            usrp,
            tx_streamer,
            rx_streamer,
            quit_event,
            result_queue,
            at_time=start_next_cmd,
        )

        # Retrieve loopback phase result
        phi_LB = result_queue.get()

        # Print loopback phase
        logger.info("Phase pilot reference signal in rad: %s", phi_LB)
        logger.info("Phase pilot reference signal in degrees: %s", np.rad2deg(phi_LB))

        start_next_cmd += cmd_time + 2.0  # Schedule next command

        # -------------------------------------------------------------------------
        # STEP 3: Load cable phase correction from YAML configuration (if available)
        # -------------------------------------------------------------------------
        phi_cable = 0
        with open(os.path.join(os.path.dirname(__file__), "phase-reference-calibration.yml"), "r") as phases_yaml:
            try:
                phases_dict = yaml.safe_load(phases_yaml)
                if HOSTNAME in phases_dict.keys():
                    phi_cable = phases_dict[HOSTNAME]
                    logger.debug(f"Applying phase correction: {phi_cable}")
                else:
                    logger.error("Phase offset not found in phase-reference-calibration.yml")
            except yaml.YAMLError as exc:
                print(exc)

        # -------------------------------------------------------------------------
        # STEP 4: Add additional phase to ensure right measurement with the scope
        # -------------------------------------------------------------------------
        phi_offset = 0
        with open(os.path.join(os.path.dirname(__file__), "config-phase-offsets.yml"), "r") as phases_yaml:
            try:
                phases_dict = yaml.safe_load(phases_yaml)
                if HOSTNAME in phases_dict.keys():
                    phi_cable = phases_dict[HOSTNAME]
                    logger.debug(f"Applying phase correction: {phi_offset}")
                else:
                    logger.error("Phase offset not found in config-phase-offsets.yml")
            except yaml.YAMLError as exc:
                print(exc)

        # -------------------------------------------------------------------------
        # STEP 5: Benchmark without phase-aligned beamforming
        # -------------------------------------------------------------------------
        
        alive_socket = context.socket(zmq.REQ)
        alive_socket.connect(f"tcp://{server_ip}:{5558}")
        logger.debug("Sending TX MODE")
        alive_socket.send_string(f"{HOSTNAME} TX")
        alive_socket.close()

        phase_corr=phi_LB - np.deg2rad(phi_cable) + np.deg2rad(phi_offset)
        logger.info("Phase correction in rad: %s", phase_corr)
        logger.info("Phase correction in degrees: %s", np.rad2deg(phase_corr))

        tx_phase_coh(
            usrp,
            tx_streamer,
            quit_event,
            # phase_corr=phi_LB + phi_P + np.deg2rad(phi_cable),
            phase_corr=phi_LB - np.deg2rad(phi_cable) + np.deg2rad(phi_offset),
            at_time=start_next_cmd,
            long_time=False, # Set long_time True if you want to transmit longer than 10 seconds
        )

        print("DONE")

    except Exception as e:
        # Handle any exception gracefully
        logger.debug("Sending signal to stop!")
        logger.error(e)
        quit_event.set()

    finally:
        # Allow threads and streams to close properly
        time.sleep(1)
        sys.exit(0)

if __name__ == "__main__":
    while 1:
        main()
