from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


EXPERIMENTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXPERIMENTS_DIR))


COORDINATOR_PATH = (
    EXPERIMENTS_DIR
    / "50_t05_t08_state_characterization"
    / "server"
    / "coordinator.py"
)
SPEC = importlib.util.spec_from_file_location("exp50_coordinator", COORDINATOR_PATH)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import machinery guard
    raise RuntimeError(f"cannot load {COORDINATOR_PATH}")
COORDINATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COORDINATOR)


class Experiment50CoordinatorTests(unittest.TestCase):
    def test_common_first_sample_time_is_accepted(self) -> None:
        errors, spread = COORDINATOR.validate_capture_alignment(
            {"T05": 12.0, "T06": 12.0, "T07": 12.0, "T08": 12.0},
            start_time_s=12.0,
            tolerance_s=4e-6,
        )
        self.assertEqual(errors, {"T05": 0.0, "T06": 0.0, "T07": 0.0, "T08": 0.0})
        self.assertEqual(spread, 0.0)

    def test_misaligned_capture_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "not aligned"):
            COORDINATOR.validate_capture_alignment(
                {"T05": 12.0, "T06": 12.0, "T07": 12.0, "T08": 12.00001},
                start_time_s=12.0,
                tolerance_s=4e-6,
            )


if __name__ == "__main__":
    unittest.main()
