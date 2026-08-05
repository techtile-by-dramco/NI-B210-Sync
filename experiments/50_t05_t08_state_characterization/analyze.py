#!/usr/bin/env python3
"""Summarize state-characterization JSONL files using circular statistics."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np


EXPERIMENTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXPERIMENTS_DIR))

from t05_t08_common.phase import circular_mean, circular_std, wrap_phase
from t05_t08_common.results import read_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=Path("state_summary.csv"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    groups: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)
    failed: dict[tuple[str, str, str, str], int] = defaultdict(int)
    for path in args.inputs:
        for record in read_jsonl(path):
            if record.get("type") != "measurement":
                continue
            key = (
                str(record["tile"]),
                str(record["mode"]),
                str(record["event"]),
                str(record["stage"]),
            )
            if record.get("status") == "ok":
                groups[key].append(float(record["phase"]["phase_rad"]))
            else:
                failed[key] += 1

    before_means: dict[tuple[str, str, str], float] = {}
    for (tile, mode, event, stage), values in groups.items():
        if stage == "before" and values:
            before_means[(tile, mode, event)] = circular_mean(np.asarray(values))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            (
                "tile",
                "mode",
                "event",
                "stage",
                "successful_runs",
                "failed_runs",
                "circular_mean_deg",
                "circular_std_deg",
                "jump_from_before_deg",
            )
        )
        for key in sorted(set(groups) | set(failed)):
            values = np.asarray(groups.get(key, []), dtype=float)
            tile, mode, event, stage = key
            mean = circular_mean(values) if values.size else np.nan
            std = circular_std(values) if values.size else np.nan
            before = before_means.get((tile, mode, event))
            jump = (
                np.rad2deg(wrap_phase(mean - before))
                if before is not None and values.size
                else np.nan
            )
            writer.writerow(
                (
                    tile,
                    mode,
                    event,
                    stage,
                    values.size,
                    failed.get(key, 0),
                    np.rad2deg(mean),
                    np.rad2deg(std),
                    jump,
                )
            )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
