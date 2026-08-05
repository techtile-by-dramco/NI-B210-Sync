#!/usr/bin/env python3
"""Start Experiment 52's continuous T04 RF source using the local config."""

from __future__ import annotations

import sys
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
EXPERIMENTS_DIR = EXPERIMENT_DIR.parent
sys.path.insert(0, str(EXPERIMENTS_DIR))

from t05_t08_common.run_t04_source import main as source_main


def main() -> int:
    if not any(
        argument == "--config" or argument.startswith("--config=")
        for argument in sys.argv[1:]
    ):
        sys.argv[1:1] = ["--config", str(EXPERIMENT_DIR / "config.yml")]
    return source_main()


if __name__ == "__main__":
    raise SystemExit(main())
