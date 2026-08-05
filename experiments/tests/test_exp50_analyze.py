from __future__ import annotations

import csv
import importlib.util
import math
import sys
import tempfile
import unittest
from pathlib import Path


EXPERIMENTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXPERIMENTS_DIR))

from t05_t08_common.results import append_jsonl


ANALYZE_PATH = (
    EXPERIMENTS_DIR / "50_t05_t08_state_characterization" / "processing" / "analyze.py"
)
SPEC = importlib.util.spec_from_file_location("exp50_analyze", ANALYZE_PATH)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import machinery guard
    raise RuntimeError(f"cannot load {ANALYZE_PATH}")
ANALYZE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYZE)


def measurement(phase_deg: float, repeat: int) -> dict:
    return {
        "type": "measurement",
        "tile": "T05",
        "mode": "external_pair",
        "event": "lo_retune",
        "stage": "before" if repeat < 2 else "after",
        "repeat": repeat % 2,
        "status": "ok",
        "phase": {
            "phase_rad": math.radians(phase_deg),
            "circular_std_rad": math.radians(0.25),
            "amplitude": 0.5,
            "residual_rms": 0.05,
            "sample_count": 8192,
            "block_count": 2,
        },
    }


class Experiment50AnalysisTests(unittest.TestCase):
    def test_wrapped_paired_jump_summary_and_figures(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            input_path = base / "run.jsonl"
            for repeat, phase_deg in enumerate((170.0, 175.0, -170.0, -165.0)):
                append_jsonl(input_path, measurement(phase_deg, repeat))
            append_jsonl(
                input_path,
                {
                    "type": "measurement",
                    "tile": "T05",
                    "mode": "external_pair",
                    "event": "lo_retune",
                    "stage": "after",
                    "repeat": 2,
                    "status": "failed",
                    "error": "synthetic timeout",
                },
            )

            successful, failed, jumps, observations = ANALYZE.load_measurements(
                [input_path]
            )
            rows = ANALYZE.summarize(successful, failed, jumps)
            after = next(row for row in rows if row["stage"] == "after")
            self.assertAlmostEqual(after["jump_from_before_deg"], 20.0, places=10)
            self.assertEqual(after["paired_event_runs"], 1)
            self.assertEqual(after["successful_runs"], 2)
            self.assertEqual(after["failed_runs"], 1)
            self.assertAlmostEqual(after["success_fraction"], 2 / 3)
            self.assertAlmostEqual(after["correlation_quality_mean_db"], 20.0)

            csv_path = base / "state_summary.csv"
            ANALYZE.write_summary(csv_path, rows)
            with csv_path.open(encoding="utf-8", newline="") as stream:
                written = list(csv.DictReader(stream))
            self.assertEqual(len(written), 2)
            self.assertIn("within_capture_circular_std_mean_deg", written[0])

            try:
                import matplotlib  # noqa: F401
            except ModuleNotFoundError:
                return
            figures = ANALYZE.create_figures(observations, rows, base / "figures")
            self.assertEqual(len(figures), 3)
            for figure in figures:
                self.assertTrue(figure.is_file())
                self.assertGreater(figure.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
