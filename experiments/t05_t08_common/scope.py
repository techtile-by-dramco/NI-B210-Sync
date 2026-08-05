"""Tektronix waveform capture for relative coherent-power measurements."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np


@dataclass(frozen=True)
class ScopePower:
    rms_voltage_v: float
    power_w: float
    power_dbm: float
    peak_voltage_v: float
    sample_count: int

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


@dataclass(frozen=True)
class ScopePhasePower:
    power: ScopePower
    signal_minus_reference_phase_rad: float

    def to_dict(self) -> dict[str, float | int]:
        result = self.power.to_dict()
        result["signal_minus_reference_phase_rad"] = (
            self.signal_minus_reference_phase_rad
        )
        result["signal_minus_reference_phase_deg"] = float(
            np.rad2deg(self.signal_minus_reference_phase_rad)
        )
        return result


def waveform_power(voltage: np.ndarray, impedance_ohm: float = 50.0) -> ScopePower:
    values = np.asarray(voltage, dtype=float).reshape(-1)
    if values.size == 0:
        raise ValueError("scope returned an empty waveform")
    ac = values - np.mean(values)
    rms = float(np.sqrt(np.mean(ac**2)))
    power_w = rms**2 / float(impedance_ohm)
    power_dbm = float(10.0 * np.log10(max(power_w, np.finfo(float).tiny) / 1e-3))
    return ScopePower(
        rms_voltage_v=rms,
        power_w=power_w,
        power_dbm=power_dbm,
        peak_voltage_v=float(np.max(np.abs(ac))),
        sample_count=int(values.size),
    )


def waveform_relative_phase(
    signal: np.ndarray,
    reference: np.ndarray,
    sample_interval_s: float,
    rf_frequency_hz: float,
) -> float:
    """Return signal minus reference phase from simultaneous real waveforms."""

    signal_values = np.asarray(signal, dtype=float).reshape(-1)
    reference_values = np.asarray(reference, dtype=float).reshape(-1)
    count = min(signal_values.size, reference_values.size)
    if count == 0:
        raise ValueError("scope returned an empty waveform")
    if sample_interval_s <= 0:
        raise ValueError("scope sample interval must be positive")
    if rf_frequency_hz >= 0.45 / sample_interval_s:
        raise ValueError("scope sample rate is too low for the requested RF correlation")
    indexes = np.arange(count, dtype=float)
    kernel = np.exp(-2j * np.pi * rf_frequency_hz * sample_interval_s * indexes)
    signal_values = signal_values[:count] - np.mean(signal_values[:count])
    reference_values = reference_values[:count] - np.mean(reference_values[:count])
    signal_phasor = np.sum(signal_values * kernel)
    reference_phasor = np.sum(reference_values * kernel)
    if abs(signal_phasor) == 0 or abs(reference_phasor) == 0:
        raise ValueError("scope RF correlation is zero; relative phase is undefined")
    return float(np.angle(signal_phasor * np.conj(reference_phasor)))


def capture_scope_power(
    resource: str,
    *,
    channel: str = "CH1",
    points: int = 100_000,
    timeout_ms: int = 10_000,
    impedance_ohm: float = 50.0,
) -> ScopePower:
    """Capture one Tektronix channel and calculate power into 50 ohms."""

    try:
        import pyvisa
    except ModuleNotFoundError as exc:
        raise RuntimeError("PyVISA is required for automatic scope capture") from exc

    manager = pyvisa.ResourceManager()
    instrument = manager.open_resource(resource)
    instrument.timeout = timeout_ms
    try:
        instrument.write("HEADER 0")
        instrument.write(f"{channel}:TERMINATION {impedance_ohm:g}")
        instrument.write(f"SELECT:{channel} 1")
        instrument.write(f"DATA:SOURCE {channel}")
        instrument.write("DATA:ENCDG RIBINARY")
        instrument.write("DATA:WIDTH 1")
        instrument.write("DATA:START 1")
        instrument.write(f"DATA:STOP {int(points)}")
        instrument.write("ACQUIRE:STOPAFTER SEQUENCE")
        instrument.write("ACQUIRE:STATE RUN")
        instrument.query("*OPC?")

        y_multiplier = float(instrument.query("WFMOUTPRE:YMULT?"))
        y_offset = float(instrument.query("WFMOUTPRE:YOFF?"))
        y_zero = float(instrument.query("WFMOUTPRE:YZERO?"))
        raw = instrument.query_binary_values(
            "CURVE?", datatype="b", container=np.asarray
        )
        voltage = (raw - y_offset) * y_multiplier + y_zero
        return waveform_power(voltage, impedance_ohm)
    finally:
        instrument.close()
        manager.close()


def capture_scope_phase_power(
    resource: str,
    *,
    signal_channel: str,
    reference_channel: str,
    rf_frequency_hz: float,
    points: int = 100_000,
    timeout_ms: int = 10_000,
    impedance_ohm: float = 50.0,
) -> ScopePhasePower:
    """Capture two channels in one acquisition and correlate them at RF."""

    try:
        import pyvisa
    except ModuleNotFoundError as exc:
        raise RuntimeError("PyVISA is required for automatic scope capture") from exc

    manager = pyvisa.ResourceManager()
    instrument = manager.open_resource(resource)
    instrument.timeout = timeout_ms

    def configure_channel(channel: str) -> None:
        instrument.write(f"{channel}:TERMINATION {impedance_ohm:g}")
        instrument.write(f"SELECT:{channel} 1")

    def read_channel(channel: str) -> tuple[np.ndarray, float]:
        instrument.write(f"DATA:SOURCE {channel}")
        y_multiplier = float(instrument.query("WFMOUTPRE:YMULT?"))
        y_offset = float(instrument.query("WFMOUTPRE:YOFF?"))
        y_zero = float(instrument.query("WFMOUTPRE:YZERO?"))
        x_increment = float(instrument.query("WFMOUTPRE:XINCR?"))
        raw = instrument.query_binary_values(
            "CURVE?", datatype="b", container=np.asarray
        )
        return (raw - y_offset) * y_multiplier + y_zero, x_increment

    try:
        instrument.write("HEADER 0")
        configure_channel(signal_channel)
        configure_channel(reference_channel)
        instrument.write("DATA:ENCDG RIBINARY")
        instrument.write("DATA:WIDTH 1")
        instrument.write("DATA:START 1")
        instrument.write(f"DATA:STOP {int(points)}")
        instrument.write("ACQUIRE:STOPAFTER SEQUENCE")
        instrument.write("ACQUIRE:STATE RUN")
        instrument.query("*OPC?")
        signal, signal_increment = read_channel(signal_channel)
        reference, reference_increment = read_channel(reference_channel)
        if not np.isclose(signal_increment, reference_increment, rtol=0.0, atol=1e-18):
            raise RuntimeError("scope channels returned different time increments")
        count = min(signal.size, reference.size)
        relative_phase = waveform_relative_phase(
            signal[:count], reference[:count], signal_increment, rf_frequency_hz
        )
        return ScopePhasePower(
            waveform_power(signal[:count], impedance_ohm), relative_phase
        )
    finally:
        instrument.close()
        manager.close()
