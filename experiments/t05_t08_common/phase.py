"""Narrowband phase estimators matching the manuscript's correlation model."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np


def wrap_phase(angle_rad: float | np.ndarray) -> float | np.ndarray:
    """Wrap radians to the half-open interval [-pi, pi)."""

    wrapped = (np.asarray(angle_rad) + np.pi) % (2 * np.pi) - np.pi
    if np.ndim(angle_rad) == 0:
        return float(wrapped)
    return wrapped


def circular_mean(angles_rad: np.ndarray) -> float:
    angles = np.asarray(angles_rad, dtype=float)
    if angles.size == 0:
        raise ValueError("cannot calculate a circular mean of an empty array")
    return float(np.angle(np.mean(np.exp(1j * angles))))


def circular_std(angles_rad: np.ndarray) -> float:
    angles = np.asarray(angles_rad, dtype=float)
    if angles.size == 0:
        raise ValueError("cannot calculate a circular standard deviation of an empty array")
    resultant = float(np.abs(np.mean(np.exp(1j * angles))))
    resultant = min(1.0, max(np.finfo(float).tiny, resultant))
    if resultant > 1.0 - 1e-15:
        return 0.0
    return float(np.sqrt(-2.0 * np.log(resultant)))


@dataclass(frozen=True)
class PhaseEstimate:
    phase_rad: float
    circular_std_rad: float
    amplitude: float
    residual_rms: float
    sample_count: int
    block_count: int

    @property
    def phase_deg(self) -> float:
        return float(np.rad2deg(self.phase_rad))

    @property
    def circular_std_deg(self) -> float:
        return float(np.rad2deg(self.circular_std_rad))

    def to_dict(self) -> dict[str, float | int]:
        result = asdict(self)
        result["phase_deg"] = self.phase_deg
        result["circular_std_deg"] = self.circular_std_deg
        return result


def _block_phasors(
    observed: np.ndarray,
    reference: np.ndarray,
    block_size: int,
) -> np.ndarray:
    usable = min(observed.size, reference.size)
    if usable < block_size:
        raise ValueError(
            f"need at least one complete block ({block_size} samples), got {usable}"
        )
    usable -= usable % block_size
    observed_blocks = observed[:usable].reshape(-1, block_size)
    reference_blocks = reference[:usable].reshape(-1, block_size)
    return np.sum(observed_blocks * np.conj(reference_blocks), axis=1)


def _estimate_from_phasors(
    phasors: np.ndarray,
    observed: np.ndarray,
    fitted_reference: np.ndarray,
) -> PhaseEstimate:
    valid = np.abs(phasors) > np.finfo(float).tiny
    if not np.any(valid):
        raise ValueError("correlation is zero; phase is undefined")
    phase_blocks = np.angle(phasors[valid])
    phase = circular_mean(phase_blocks)
    amplitude = float(np.sum(np.abs(phasors[valid])) / fitted_reference.size)
    unit_reference = fitted_reference / np.maximum(
        np.abs(fitted_reference), np.finfo(float).tiny
    )
    fitted = amplitude * unit_reference * np.exp(1j * phase)
    residual = observed[: fitted.size] - fitted
    return PhaseEstimate(
        phase_rad=phase,
        circular_std_rad=circular_std(phase_blocks),
        amplitude=amplitude,
        residual_rms=float(np.sqrt(np.mean(np.abs(residual) ** 2))),
        sample_count=int(fitted.size),
        block_count=int(phase_blocks.size),
    )


def estimate_tone(
    samples: np.ndarray,
    sample_rate_hz: float,
    tone_frequency_hz: float,
    *,
    discard_samples: int = 0,
    block_size: int = 4096,
) -> PhaseEstimate:
    """Estimate a tone phase using arg(sum(y[n] * conj(x[n])))."""

    samples = np.asarray(samples, dtype=np.complex128).reshape(-1)
    if discard_samples < 0:
        raise ValueError("discard_samples cannot be negative")
    observed = samples[discard_samples:]
    indexes = np.arange(observed.size, dtype=float) + discard_samples
    reference = np.exp(2j * np.pi * float(tone_frequency_hz) * indexes / sample_rate_hz)
    phasors = _block_phasors(observed, reference, block_size)
    usable = phasors.size * block_size
    return _estimate_from_phasors(phasors, observed[:usable], reference[:usable])


def estimate_relative_phase(
    reference_samples: np.ndarray,
    observed_samples: np.ndarray,
    *,
    discard_samples: int = 0,
    block_size: int = 4096,
) -> PhaseEstimate:
    """Estimate reference minus observed phase from simultaneous I/Q samples."""

    reference = np.asarray(reference_samples, dtype=np.complex128).reshape(-1)
    observed = np.asarray(observed_samples, dtype=np.complex128).reshape(-1)
    usable = min(reference.size, observed.size)
    reference = reference[discard_samples:usable]
    observed = observed[discard_samples:usable]
    # Normalize the observed waveform so amplitude reports the reference-path
    # amplitude instead of the product of both path amplitudes.
    observed_unit = observed / np.maximum(
        np.abs(observed), np.finfo(float).tiny
    )
    phasors = _block_phasors(reference, observed_unit, block_size)
    fitted_size = phasors.size * block_size
    return _estimate_from_phasors(
        phasors,
        reference[:fitted_size],
        observed_unit[:fitted_size],
    )


def beamforming_correction(
    reference_minus_pilot_rad: float,
    reference_minus_loopback_rad: float,
    reference_cable_phase_rad: float,
) -> float:
    """Return the manuscript's narrowband transmit correction.

    With measured d_p = R-P and d_l = R-L, the manuscript expression
    -(2*cable + (P-R) + (L-R)) becomes d_p + d_l - 2*cable.
    """

    return wrap_phase(
        reference_minus_pilot_rad
        + reference_minus_loopback_rad
        - 2.0 * reference_cable_phase_rad
    )
