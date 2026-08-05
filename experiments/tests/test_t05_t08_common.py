from __future__ import annotations

import math
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


EXPERIMENTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXPERIMENTS_DIR))

from t05_t08_common.config import load_config, resolve_tile, validate_common_config
from t05_t08_common.phase import (
    beamforming_correction,
    estimate_relative_phase,
    estimate_tone,
    wrap_phase,
)
from t05_t08_common.scope import waveform_power, waveform_relative_phase


class PhaseTests(unittest.TestCase):
    def test_tone_correlation_recovers_phase_and_amplitude(self) -> None:
        sample_rate = 250_000.0
        tone_frequency = 1_000.0
        phase = 0.73
        amplitude = 0.4
        count = 16_384
        indexes = np.arange(count)
        samples = amplitude * np.exp(
            1j * (2 * np.pi * tone_frequency * indexes / sample_rate + phase)
        )
        estimate = estimate_tone(
            samples, sample_rate, tone_frequency, block_size=2_048
        )
        self.assertAlmostEqual(estimate.phase_rad, phase, places=10)
        self.assertAlmostEqual(estimate.amplitude, amplitude, places=10)
        self.assertLess(estimate.circular_std_rad, 1e-7)
        self.assertLess(estimate.residual_rms, 1e-10)

    def test_relative_phase_is_reference_minus_observed(self) -> None:
        indexes = np.arange(8_192)
        carrier = np.exp(1j * 0.07 * indexes)
        reference = 0.6 * carrier * np.exp(1j * 0.4)
        observed = 0.2 * carrier * np.exp(-1j * 0.2)
        estimate = estimate_relative_phase(reference, observed, block_size=1_024)
        self.assertAlmostEqual(estimate.phase_rad, 0.6, places=10)
        self.assertAlmostEqual(estimate.amplitude, 0.6, places=10)
        self.assertLess(estimate.residual_rms, 1e-10)

    def test_manuscript_correction_signs(self) -> None:
        result = beamforming_correction(0.4, -0.1, 0.05)
        self.assertAlmostEqual(result, 0.2)
        self.assertAlmostEqual(wrap_phase(3 * math.pi), -math.pi)


class ConfigTests(unittest.TestCase):
    def test_hostname_resolution(self) -> None:
        self.assertEqual(resolve_tile(hostname="rpi-T07"), "T07")
        with self.assertRaises(ValueError):
            resolve_tile(hostname="laboratory-pc")

    def test_load_and_validate(self) -> None:
        content = """
tiles: [T05, T06, T07, T08]
rf_source_tile: T04
rf_source_tx_channel: 0
rf_source_tx_antenna: TX/RX
rf_source_tone_amplitude: 0.2
center_frequency_hz: 920000000
tone_frequency_hz: 1000
sample_rate_hz: 250000
master_clock_rate_hz: 20000000
rf_bandwidth_hz: 200000
clock_source: external
time_source: external
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yml"
            path.write_text(content, encoding="utf-8")
            config = load_config(path)
        validate_common_config(config)

    def test_only_t04_is_accepted_as_the_5x_rf_source(self) -> None:
        config = {
            "tiles": ["T05", "T06", "T07", "T08"],
            "rf_source_tile": "T03",
            "rf_source_tx_channel": 0,
            "rf_source_tx_antenna": "TX/RX",
            "rf_source_tone_amplitude": 0.2,
            "center_frequency_hz": 920e6,
            "tone_frequency_hz": 1e3,
            "sample_rate_hz": 250e3,
            "master_clock_rate_hz": 20e6,
            "rf_bandwidth_hz": 200e3,
            "clock_source": "external",
            "time_source": "external",
        }
        with self.assertRaisesRegex(ValueError, "must be T04"):
            validate_common_config(config)


class ScopeTests(unittest.TestCase):
    def test_waveform_power_into_50_ohms(self) -> None:
        # A 1 V peak sine is 1/sqrt(2) Vrms and therefore 10 mW / 10 dBm.
        phase = np.linspace(0, 20 * np.pi, 100_000, endpoint=False)
        measured = waveform_power(np.sin(phase))
        self.assertAlmostEqual(measured.rms_voltage_v, 1 / math.sqrt(2), places=6)
        self.assertAlmostEqual(measured.power_dbm, 10.0, places=6)

    def test_waveform_relative_phase(self) -> None:
        sample_rate = 10_000.0
        frequency = 1_000.0
        indexes = np.arange(10_000)
        signal = np.cos(2 * np.pi * frequency * indexes / sample_rate + 0.7)
        reference = np.cos(2 * np.pi * frequency * indexes / sample_rate - 0.2)
        phase = waveform_relative_phase(
            signal, reference, 1.0 / sample_rate, frequency
        )
        self.assertAlmostEqual(phase, 0.9, places=10)


if __name__ == "__main__":
    unittest.main()
