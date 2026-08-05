from __future__ import annotations

import csv
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


EXPERIMENTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXPERIMENTS_DIR))


ANALYZE_PATH = (
    EXPERIMENTS_DIR
    / "60_t05_t08_zmq_gpio_arrival"
    / "processing"
    / "analyze_scope.py"
)
SPEC = importlib.util.spec_from_file_location("exp60_scope_analysis", ANALYZE_PATH)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import machinery guard
    raise RuntimeError(f"cannot load {ANALYZE_PATH}")
ANALYZE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYZE)


class Experiment60ScopeAnalysisTests(unittest.TestCase):
    def test_interpolated_rising_edges_and_skew_summary(self) -> None:
        time_s = np.arange(16, dtype=float) * 1e-6
        starts = {"T05": 2, "T06": 3, "T07": 4, "T08": 5}
        waveforms = {
            tile: np.where(np.arange(time_s.size) >= start, 3.3, 0.0)
            for tile, start in starts.items()
        }

        edges = {
            tile: ANALYZE.rising_edges(time_s, waveform, 1.65, 0.1)
            for tile, waveform in waveforms.items()
        }
        self.assertAlmostEqual(edges["T05"][0], 1.5e-6)
        self.assertAlmostEqual(edges["T08"][0], 4.5e-6)

        rows = [
            {
                "T06_minus_T05_us": 1.0,
                "T07_minus_T05_us": 2.0,
                "T08_minus_T05_us": 3.0,
                "peak_to_peak_skew_us": 3.0,
            },
            {
                "T06_minus_T05_us": 2.0,
                "T07_minus_T05_us": 4.0,
                "T08_minus_T05_us": 6.0,
                "peak_to_peak_skew_us": 6.0,
            },
        ]
        summary = ANALYZE.summary_rows(rows)
        t06 = next(row for row in summary if row["tile"] == "T06")
        skew = next(row for row in summary if row["kind"] == "four_tile_peak_to_peak_skew")
        self.assertEqual(t06["count"], 2)
        self.assertAlmostEqual(t06["mean_us"], 1.5)
        self.assertAlmostEqual(skew["max_us"], 6.0)

    def test_csv_edge_sets_are_paired_by_simultaneous_scope_record(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "scope.csv"
            with input_path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(
                    stream, fieldnames=["time_s", "CH1", "CH2", "CH3", "CH4"]
                )
                writer.writeheader()
                for sample in range(20):
                    writer.writerow(
                        {
                            "time_s": sample * 1e-6,
                            "CH1": 3.3 if sample >= 2 else 0.0,
                            "CH2": 3.3 if sample >= 3 else 0.0,
                            "CH3": 3.3 if sample >= 4 else 0.0,
                            "CH4": 3.3 if sample >= 5 else 0.0,
                        }
                    )

            rows, mismatches = ANALYZE.build_edge_rows(
                [input_path],
                time_column="time_s",
                channels={"T05": "CH1", "T06": "CH2", "T07": "CH3", "T08": "CH4"},
                threshold_v=1.65,
                min_separation_s=0.1,
            )
            self.assertEqual(mismatches, [])
            self.assertEqual(len(rows), 1)
            self.assertAlmostEqual(rows[0]["T08_minus_T05_us"], 3.0)
            self.assertAlmostEqual(rows[0]["peak_to_peak_skew_us"], 3.0)


if __name__ == "__main__":
    unittest.main()

