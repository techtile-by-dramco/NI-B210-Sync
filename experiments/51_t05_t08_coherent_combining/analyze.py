#!/usr/bin/env python3
"""Aggregate coherent-combining power and compare M and M-squared scaling."""

from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path


EXPERIMENTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXPERIMENTS_DIR))

from t05_t08_common.phase import circular_mean, circular_std, wrap_phase
from t05_t08_common.results import read_jsonl


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("combining_summary.csv"))
    args = parser.parse_args()
    grouped: dict[tuple[str, int], list[float]] = defaultdict(list)
    records = read_jsonl(args.input)
    individual_watts_by_tile: dict[str, list[float]] = defaultdict(list)
    for record in records:
        if record.get("type") == "individual_power":
            individual_watts_by_tile[str(record["tile"])].append(
                1e-3 * 10 ** (float(record["power_dbm"]) / 10.0)
            )
    individual_watts_mean = {
        tile: statistics.mean(values)
        for tile, values in individual_watts_by_tile.items()
    }
    for record in records:
        if record.get("type") == "power_measurement":
            grouped[(str(record["mode"]), int(record["transmitter_count"]))].append(
                float(record["power_dbm"])
            )

    baselines = {
        mode: statistics.mean(values)
        for (mode, count), values in grouped.items()
        if count == 1
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            (
                "mode",
                "transmitter_count",
                "runs",
                "mean_power_dbm",
                "std_power_db",
                "gain_from_single_db",
                "ideal_coherent_gain_db",
                "ideal_incoherent_gain_db",
                "coherent_gain_error_db",
                "amplitude_aware_coherent_power_dbm",
                "amplitude_aware_incoherent_power_dbm",
                "amplitude_aware_coherent_error_db",
            )
        )
        for (mode, count), values in sorted(grouped.items()):
            mean = statistics.mean(values)
            std = statistics.stdev(values) if len(values) > 1 else 0.0
            gain = mean - baselines[mode]
            ideal_coherent = 20.0 * math.log10(count)
            ideal_incoherent = 10.0 * math.log10(count)
            active_tiles = ("T05", "T06", "T07", "T08")[:count]
            individual_watts = [
                individual_watts_mean[tile]
                for tile in active_tiles
                if tile in individual_watts_mean
            ]
            if len(individual_watts) == count:
                coherent_watts = sum(math.sqrt(value) for value in individual_watts) ** 2
                incoherent_watts = sum(individual_watts)
                coherent_dbm = 10.0 * math.log10(coherent_watts / 1e-3)
                incoherent_dbm = 10.0 * math.log10(incoherent_watts / 1e-3)
                amplitude_error = mean - coherent_dbm
            else:
                coherent_dbm = math.nan
                incoherent_dbm = math.nan
                amplitude_error = math.nan
            writer.writerow(
                (
                    mode,
                    count,
                    len(values),
                    mean,
                    std,
                    gain,
                    ideal_coherent,
                    ideal_incoherent,
                    gain - ideal_coherent,
                    coherent_dbm,
                    incoherent_dbm,
                    amplitude_error,
                )
            )
    residual_path = args.output.with_name(args.output.stem + "_residual_phase.csv")
    phase_by_tile: dict[str, list[float]] = defaultdict(list)
    for record in records:
        if (
            record.get("type") == "individual_power"
            and "signal_minus_reference_phase_rad" in record
        ):
            phase_by_tile[str(record["tile"])].append(
                float(record["signal_minus_reference_phase_rad"])
            )
    with residual_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            (
                "tile",
                "observed_phase_deg",
                "residual_from_array_mean_deg",
                "per_tile_circular_std_deg",
                "array_circular_std_deg",
            )
        )
        if phase_by_tile:
            tile_means = {
                tile: circular_mean(values) for tile, values in phase_by_tile.items()
            }
            mean = circular_mean(list(tile_means.values()))
            std = circular_std(list(tile_means.values()))
            for tile, phase in sorted(tile_means.items()):
                writer.writerow(
                    (
                        tile,
                        math.degrees(phase),
                        math.degrees(wrap_phase(phase - mean)),
                        math.degrees(circular_std(phase_by_tile[tile])),
                        math.degrees(std),
                    )
                )
    print(args.output)
    print(residual_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
