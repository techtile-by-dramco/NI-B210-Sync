"""Minimal UHD adapter used by the new T05--T08 experiments.

The UHD import is deliberately lazy so planning, analysis, and unit tests work on
machines that do not have the NI/Ettus Python bindings installed.
"""

from __future__ import annotations

import hashlib
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


class RadioError(RuntimeError):
    """Raised when a run cannot be interpreted as a valid phase observation."""


@dataclass(frozen=True)
class Capture:
    samples: np.ndarray
    first_sample_time_s: float | None
    overflow_count: int
    timeout_count: int


def _uhd():
    try:
        import uhd  # type: ignore
    except ModuleNotFoundError as exc:
        raise RadioError(
            "The UHD Python bindings are missing. Run this command on a testbench "
            "Raspberry Pi with the repository's UHD environment loaded."
        ) from exc
    return uhd


def _sensor_bool(sensor: Any) -> bool:
    return bool(sensor.to_bool() if hasattr(sensor, "to_bool") else sensor)


class B210Session:
    """One configured B210 lock interval."""

    LOOPBACK_REGISTER = 0
    LOOPBACK_ENABLED = 0x00000006
    LOOPBACK_DISABLED = 0x00000000

    def __init__(self, config: dict[str, Any], tile: str):
        self.config = config
        self.tile = tile
        self.uhd = _uhd()
        args = ["type=b200", "mode_n=integer"]
        fpga_path = config.get("loopback_fpga")
        if fpga_path:
            resolved = Path(fpga_path).expanduser().resolve()
            if not resolved.is_file():
                raise RadioError(f"custom loopback FPGA image not found: {resolved}")
            args.extend(("enable_user_regs", f"fpga={resolved}"))
        self.usrp = self.uhd.usrp.MultiUSRP(",".join(args))
        self.reference_channel = int(config.get("reference_channel", 0))
        self.measured_channel = int(config.get("measured_channel", 1))
        if self.reference_channel == self.measured_channel:
            raise RadioError("reference_channel and measured_channel must differ")
        self.channels = [self.reference_channel, self.measured_channel]
        self._configure()

    def _configure(self) -> None:
        cfg = self.config
        self.usrp.set_master_clock_rate(float(cfg["master_clock_rate_hz"]))
        self.usrp.set_clock_source(str(cfg["clock_source"]))
        self.usrp.set_time_source(str(cfg["time_source"]))
        self._wait_for_reference_lock(float(cfg.get("lock_timeout_s", 5.0)))

        for channel in self.channels:
            self.usrp.set_rx_rate(float(cfg["sample_rate_hz"]), channel)
            self.usrp.set_tx_rate(float(cfg["sample_rate_hz"]), channel)
            self.usrp.set_rx_bandwidth(float(cfg["rf_bandwidth_hz"]), channel)
            self.usrp.set_tx_bandwidth(float(cfg["rf_bandwidth_hz"]), channel)
            self.usrp.set_rx_agc(False, channel)
            self.usrp.set_rx_dc_offset(bool(cfg.get("rx_dc_offset", False)), channel)

        self.usrp.set_rx_gain(float(cfg["reference_rx_gain_db"]), self.reference_channel)
        self.usrp.set_rx_gain(float(cfg["measured_rx_gain_db"]), self.measured_channel)
        self.usrp.set_tx_gain(float(cfg["tx_gain_db"]), self.measured_channel)
        self.usrp.set_rx_antenna(
            str(cfg.get("reference_rx_antenna", "RX2")), self.reference_channel
        )
        self.usrp.set_rx_antenna(
            str(cfg.get("measured_rx_antenna", "TX/RX")), self.measured_channel
        )
        self.usrp.set_tx_antenna(
            str(cfg.get("measured_tx_antenna", "TX/RX")), self.measured_channel
        )
        self.synchronize_time()
        self.timed_tune(float(cfg["center_frequency_hz"]))

    def close(self) -> None:
        """Release streamers/device handles before a deliberate reopen."""

        self.usrp = None

    def metadata(self) -> dict[str, Any]:
        """Return the runtime state needed to interpret a calibration."""

        if self.usrp is None:
            raise RadioError("radio session is closed")
        try:
            uhd_version = self.uhd.get_version_string()
        except Exception:
            uhd_version = getattr(self.uhd, "__version__", "unknown")
        try:
            device_info = {
                str(key): str(value)
                for key, value in self.usrp.get_usrp_rx_info(
                    self.reference_channel
                ).items()
            }
        except Exception:
            device_info = {}
        fpga_path = self.config.get("loopback_fpga")
        fpga_sha256 = None
        if fpga_path:
            digest = hashlib.sha256()
            with Path(fpga_path).open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            fpga_sha256 = digest.hexdigest()
        return {
            "tile": self.tile,
            "uhd_version": str(uhd_version),
            "device": device_info,
            "device_description": self.usrp.get_pp_string(),
            "loopback_fpga": str(fpga_path) if fpga_path else None,
            "loopback_fpga_sha256": fpga_sha256,
            "reference_channel": self.reference_channel,
            "measured_channel": self.measured_channel,
            "actual": {
                "master_clock_rate_hz": self.usrp.get_master_clock_rate(),
                "reference_rx_rate_hz": self.usrp.get_rx_rate(self.reference_channel),
                "measured_rx_rate_hz": self.usrp.get_rx_rate(self.measured_channel),
                "measured_tx_rate_hz": self.usrp.get_tx_rate(self.measured_channel),
                "reference_rx_frequency_hz": self.usrp.get_rx_freq(
                    self.reference_channel
                ),
                "measured_rx_frequency_hz": self.usrp.get_rx_freq(
                    self.measured_channel
                ),
                "measured_tx_frequency_hz": self.usrp.get_tx_freq(
                    self.measured_channel
                ),
                "reference_rx_gain_db": self.usrp.get_rx_gain(self.reference_channel),
                "measured_rx_gain_db": self.usrp.get_rx_gain(self.measured_channel),
                "measured_tx_gain_db": self.usrp.get_tx_gain(self.measured_channel),
            },
        }

    def _wait_for_reference_lock(self, timeout_s: float) -> None:
        if self.usrp is None:
            raise RadioError("radio session is closed")
        deadline = time.monotonic() + timeout_s
        for board in range(self.usrp.get_num_mboards()):
            while time.monotonic() < deadline:
                if _sensor_bool(self.usrp.get_mboard_sensor("ref_locked", board)):
                    break
                time.sleep(0.01)
            else:
                raise RadioError(f"{self.tile}: external reference did not lock")

    def synchronize_time(self) -> None:
        """Latch device time zero on an external PPS and wait for it to occur."""

        self.usrp.set_time_unknown_pps(self.uhd.types.TimeSpec(0.0))
        time.sleep(float(self.config.get("pps_settle_s", 2.0)))

    def timed_tune(self, frequency_hz: float, lead_s: float | None = None) -> None:
        lead = float(lead_s or self.config.get("command_lead_s", 0.25))
        at_time = self.usrp.get_time_now().get_real_secs() + lead
        self._schedule_tune(frequency_hz, at_time)
        time.sleep(lead + float(self.config.get("lo_settle_s", 0.1)))
        self._verify_lo_locks()

    def _schedule_tune(self, frequency_hz: float, at_time_s: float) -> None:
        """Queue an integer-N tune for one exact B210 device time."""

        self.usrp.set_command_time(self.uhd.types.TimeSpec(float(at_time_s)))
        try:
            request = self.uhd.types.TuneRequest(float(frequency_hz))
            request.args = self.uhd.types.DeviceAddr("mode_n=integer")
            for channel in self.channels:
                self.usrp.set_rx_freq(request, channel)
                self.usrp.set_tx_freq(request, channel)
        finally:
            self.usrp.clear_command_time()

    def _verify_lo_locks(self) -> None:
        for channel in self.channels:
            for direction in ("rx", "tx"):
                getter = getattr(self.usrp, f"get_{direction}_sensor")
                try:
                    locked = _sensor_bool(getter("lo_locked", channel))
                except TypeError:
                    locked = _sensor_bool(getter("lo_locked"))
                if not locked:
                    raise RadioError(f"{self.tile}: {direction.upper()} LO is not locked")

    def _schedule_command(self, at_time_s: float, operation: Any) -> None:
        """Queue one UHD property update at an exact B210 device time."""

        self.usrp.set_command_time(self.uhd.types.TimeSpec(float(at_time_s)))
        try:
            operation()
        finally:
            self.usrp.clear_command_time()

    def schedule_state_event(self, event: str, event_time_s: float) -> float:
        """Queue a schedulable state intervention and return its completion time.

        The caller must send this command before ``event_time_s``. Reopen,
        power-cycle, and reference-cable interventions are deliberately rejected:
        their completion is controlled by a host or operator, not UHD time.
        """

        if self.usrp is None:
            raise RadioError("radio session is closed")
        event_time_s = float(event_time_s)
        if event_time_s <= self.usrp.get_time_now().get_real_secs():
            raise RadioError(f"{self.tile}: event time is not in the future")
        if event in ("fixed_repeat", "stream_restart"):
            # A new timed RX command is the stream-restart intervention.
            return event_time_s

        settle_s = float(self.config.get("event_settle_s", 0.25))
        completion_time_s = event_time_s + settle_s
        if event == "lo_retune":
            center = float(self.config["center_frequency_hz"])
            self._schedule_tune(
                center + float(self.config["retune_offset_hz"]), event_time_s
            )
            self._schedule_tune(center, completion_time_s)
        elif event == "rx_gain_change":
            nominal = float(self.config["measured_rx_gain_db"])
            changed = nominal + float(self.config["temporary_rx_gain_delta_db"])
            self._schedule_command(
                event_time_s,
                lambda: self.usrp.set_rx_gain(changed, self.measured_channel),
            )
            self._schedule_command(
                completion_time_s,
                lambda: self.usrp.set_rx_gain(nominal, self.measured_channel),
            )
        elif event == "tx_gain_change":
            nominal = float(self.config["tx_gain_db"])
            changed = nominal + float(self.config["temporary_tx_gain_delta_db"])
            self._schedule_command(
                event_time_s,
                lambda: self.usrp.set_tx_gain(changed, self.measured_channel),
            )
            self._schedule_command(
                completion_time_s,
                lambda: self.usrp.set_tx_gain(nominal, self.measured_channel),
            )
        elif event == "rx_port_change":
            nominal = str(self.config["measured_rx_antenna"])
            alternate = str(self.config["alternate_rx_antenna"])
            if nominal == alternate:
                raise RadioError("alternate_rx_antenna must differ from measured_rx_antenna")
            self._schedule_command(
                event_time_s,
                lambda: self.usrp.set_rx_antenna(alternate, self.measured_channel),
            )
            self._schedule_command(
                completion_time_s,
                lambda: self.usrp.set_rx_antenna(nominal, self.measured_channel),
            )
        else:
            raise RadioError(
                f"{event} cannot be scheduled at a common device time; "
                "run it as a documented per-tile/manual trial"
            )
        return completion_time_s

    def set_measured_rx_gain(self, gain_db: float) -> None:
        self.usrp.set_rx_gain(float(gain_db), self.measured_channel)

    def set_measured_tx_gain(self, gain_db: float) -> None:
        self.usrp.set_tx_gain(float(gain_db), self.measured_channel)

    def _rx_streamer(self):
        args = self.uhd.usrp.StreamArgs("fc32", "sc16")
        args.channels = self.channels
        return self.usrp.get_rx_stream(args)

    def _tx_streamer(self):
        args = self.uhd.usrp.StreamArgs("fc32", "sc16")
        args.channels = [self.measured_channel]
        return self.usrp.get_tx_stream(args)

    def next_start_time(self, lead_s: float | None = None) -> float:
        lead = float(lead_s or self.config.get("stream_lead_s", 0.5))
        return self.usrp.get_time_now().get_real_secs() + lead

    def capture_pair(self, duration_s: float, start_time_s: float | None = None) -> Capture:
        streamer = self._rx_streamer()
        sample_count = int(np.ceil(duration_s * float(self.config["sample_rate_hz"])))
        samples = np.empty((2, sample_count), dtype=np.complex64)
        metadata = self.uhd.types.RXMetadata()
        command = self.uhd.types.StreamCMD(self.uhd.types.StreamMode.start_cont)
        command.stream_now = False
        start_time_s = start_time_s or self.next_start_time()
        command.time_spec = self.uhd.types.TimeSpec(start_time_s)
        streamer.issue_stream_cmd(command)

        offset = 0
        first_sample_time: float | None = None
        overflow_count = 0
        timeout_count = 0
        timeout = max(1.0, start_time_s - self.usrp.get_time_now().get_real_secs() + 1.0)
        packet = np.empty((2, streamer.get_max_num_samps()), dtype=np.complex64)
        try:
            while offset < sample_count:
                received = streamer.recv(packet, metadata, timeout)
                timeout = 1.0
                if metadata.error_code == self.uhd.types.RXMetadataErrorCode.timeout:
                    timeout_count += 1
                    raise RadioError(f"{self.tile}: RX timeout")
                if metadata.error_code == self.uhd.types.RXMetadataErrorCode.overflow:
                    overflow_count += 1
                    raise RadioError(f"{self.tile}: RX overflow")
                if metadata.error_code != self.uhd.types.RXMetadataErrorCode.none:
                    raise RadioError(f"{self.tile}: RX error {metadata.strerror()}")
                if received <= 0:
                    continue
                if first_sample_time is None and metadata.has_time_spec:
                    first_sample_time = metadata.time_spec.get_real_secs()
                take = min(received, sample_count - offset)
                samples[:, offset : offset + take] = packet[:, :take]
                offset += take
        finally:
            streamer.issue_stream_cmd(
                self.uhd.types.StreamCMD(self.uhd.types.StreamMode.stop_cont)
            )

        tolerance = 1.0 / float(self.config["sample_rate_hz"])
        if first_sample_time is None or abs(first_sample_time - start_time_s) > tolerance:
            raise RadioError(
                f"{self.tile}: unexpected first-sample time {first_sample_time}; "
                f"expected {start_time_s} within {tolerance} s"
            )
        return Capture(samples, first_sample_time, overflow_count, timeout_count)

    def _tone(self, sample_count: int, phase_rad: float, amplitude: float) -> np.ndarray:
        indexes = np.arange(sample_count, dtype=np.float64)
        tone = amplitude * np.exp(
            1j
            * (
                2.0
                * np.pi
                * float(self.config["tone_frequency_hz"])
                * indexes
                / float(self.config["sample_rate_hz"])
                + phase_rad
            )
        )
        return tone.astype(np.complex64, copy=False).reshape(1, -1)

    def transmit(
        self,
        duration_s: float,
        phase_rad: float,
        start_time_s: float | None = None,
        amplitude: float | None = None,
    ) -> None:
        streamer = self._tx_streamer()
        sample_count = int(np.ceil(duration_s * float(self.config["sample_rate_hz"])))
        tone = self._tone(
            sample_count,
            phase_rad,
            float(amplitude or self.config.get("tone_amplitude", 0.5)),
        )
        metadata = self.uhd.types.TXMetadata()
        metadata.has_time_spec = True
        start_time_s = start_time_s or self.next_start_time()
        metadata.time_spec = self.uhd.types.TimeSpec(start_time_s)
        offset = 0
        while offset < sample_count:
            sent = streamer.send(tone[:, offset:], metadata, 1.0)
            if sent <= 0:
                raise RadioError(f"{self.tile}: TX send timed out")
            offset += sent
            metadata.has_time_spec = False
        metadata.end_of_burst = True
        streamer.send(np.zeros((1, 0), dtype=np.complex64), metadata)

        async_metadata = self.uhd.types.TXAsyncMetadata()
        errors: list[str] = []
        while streamer.recv_async_msg(async_metadata, 0.01):
            if async_metadata.event_code not in (
                self.uhd.types.TXMetadataEventCode.burst_ack,
            ):
                errors.append(str(async_metadata.event_code))
        if errors:
            raise RadioError(f"{self.tile}: TX asynchronous errors: {', '.join(errors)}")

    def _loopback_iface(self):
        try:
            interface = self.usrp.get_user_settings_iface(self.measured_channel)
        except Exception as exc:
            raise RadioError(
                "internal loopback requires the custom FPGA image and user-register support"
            ) from exc
        if interface is None:
            raise RadioError("UHD returned no user-settings interface for loopback")
        return interface

    def capture_internal_loopback(
        self, duration_s: float, start_time_s: float | None = None
    ) -> Capture:
        interface = self._loopback_iface()
        interface.poke32(self.LOOPBACK_REGISTER, self.LOOPBACK_ENABLED)
        start_time_s = start_time_s or self.next_start_time()
        error: list[BaseException] = []

        def transmit_worker() -> None:
            try:
                self.transmit(duration_s, 0.0, start_time_s)
            except BaseException as exc:  # propagated after joining the hardware thread
                error.append(exc)

        worker = threading.Thread(target=transmit_worker, name="loopback-tx")
        worker.start()
        try:
            capture = self.capture_pair(duration_s, start_time_s)
        finally:
            worker.join()
            interface.poke32(self.LOOPBACK_REGISTER, self.LOOPBACK_DISABLED)
        if error:
            raise RadioError(f"loopback TX failed: {error[0]}") from error[0]
        return capture
