#!/usr/bin/env python3
"""Create phase-error time series and a recalibration-oriented summary."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np


EXPERIMENTS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(EXPERIMENTS_DIR))

from t05_t08_common.phase import circular_mean, circular_std, wrap_phase
from t05_t08_common.results import read_jsonl


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output-prefix", type=Path, default=Path("stability"))
    parser.add_argument("--threshold-deg", type=float, default=5.0)
    args = parser.parse_args()
    records = []
    for path in args.inputs:
        records.extend(
            record
            for record in read_jsonl(path)
            if record.get("type") == "measurement" and record.get("status") == "ok"
        )
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for record in records:
        grouped[(record["tile"], record["mode"], record["event"])].append(record)

    time_path = args.output_prefix.with_name(args.output_prefix.name + "_timeseries.csv")
    summary_path = args.output_prefix.with_name(args.output_prefix.name + "_summary.csv")
    time_path.parent.mkdir(parents=True, exist_ok=True)
    with time_path.open("w", encoding="utf-8", newline="") as time_stream, summary_path.open(
        "w", encoding="utf-8", newline=""
    ) as summary_stream:
        time_writer = csv.writer(time_stream)
        time_writer.writerow(
            (
                "tile",
                "mode",
                "event",
                "measurement_index",
                "elapsed_s",
                "event_applied",
                "phase_deg",
                "phase_error_deg",
                "temperature_c",
            )
        )
        summary_writer = csv.writer(summary_stream)
        summary_writer.writerow(
            (
                "tile",
                "mode",
                "event",
                "runs",
                "circular_std_deg",
                "drift_deg_per_hour",
                "event_jump_deg",
                "first_threshold_crossing_s",
            )
        )
        for key, values in sorted(grouped.items()):
            values.sort(key=lambda record: int(record["measurement_index"]))
            phases = np.asarray([record["phase"]["phase_rad"] for record in values])
            elapsed = np.asarray([record["elapsed_s"] for record in values], dtype=float)
            pre_event = np.asarray(
                [not bool(record["event_applied"]) for record in values], dtype=bool
            )
            baseline_values = phases[pre_event][: min(5, np.count_nonzero(pre_event))]
            if baseline_values.size == 0:
                baseline_values = phases[: min(5, phases.size)]
            baseline = circular_mean(baseline_values)
            errors = np.asarray(wrap_phase(phases - baseline), dtype=float)
            drift_mask = pre_event if np.any(~pre_event) else np.ones_like(
                pre_event, dtype=bool
            )
            drift_elapsed = elapsed[drift_mask]
            unwrapped = np.unwrap(errors[drift_mask])
            drift = (
                float(np.polyfit(drift_elapsed, np.rad2deg(unwrapped), 1)[0] * 3600.0)
                if drift_elapsed.size > 1 and np.ptp(drift_elapsed) > 0
                else np.nan
            )
            after_event = ~pre_event
            event_jump = np.nan
            if np.any(pre_event) and np.any(after_event):
                event_jump = np.rad2deg(
                    wrap_phase(circular_mean(phases[after_event]) - circular_mean(phases[pre_event]))
                )
            crossing = np.flatnonzero(np.abs(np.rad2deg(errors)) > args.threshold_deg)
            crossing_s = elapsed[crossing[0]] if crossing.size else np.nan
            for record, phase, error in zip(values, phases, errors):
                time_writer.writerow(
                    (
                        *key,
                        record["measurement_index"],
                        record["elapsed_s"],
                        record["event_applied"],
                        np.rad2deg(phase),
                        np.rad2deg(error),
                        record.get("temperature_c"),
                    )
                )
            summary_writer.writerow(
                (
                    *key,
                    len(values),
                    np.rad2deg(circular_std(phases)),
                    drift,
                    event_jump,
                    crossing_s,
                )
            )
    print(time_path)
    print(summary_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
