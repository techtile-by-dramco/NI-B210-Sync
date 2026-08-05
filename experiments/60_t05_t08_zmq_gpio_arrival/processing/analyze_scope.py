#!/usr/bin/env python3
"""Measure simultaneous T05--T08 GPIO rising-edge skew from scope CSV exports."""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXPERIMENT_DIR))

from common import TILES, load_config, validate_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path, help="simultaneous four-channel CSV exports")
    parser.add_argument("--config", type=Path, default=EXPERIMENT_DIR / "config.yml")
    parser.add_argument("--time-column", default="time_s")
    parser.add_argument("--threshold-v", type=float)
    parser.add_argument("--min-edge-separation-s", type=float)
    parser.add_argument("--output-prefix", type=Path, default=Path("zmq_scope"))
    parser.add_argument("--no-figures", action="store_true")
    return parser.parse_args()


def load_scope_csv(
    path: Path, time_column: str, channels: dict[str, str]
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    data = np.genfromtxt(path, delimiter=",", names=True, dtype=float, encoding="utf-8")
    if data.dtype.names is None:
        raise ValueError(f"{path} has no CSV header")
    names = set(data.dtype.names)
    required = {time_column, *channels.values()}
    missing = sorted(required.difference(names))
    if missing:
        raise ValueError(f"{path} is missing CSV columns: {', '.join(missing)}")
    data = np.atleast_1d(data)
    time_s = np.asarray(data[time_column], dtype=float)
    if time_s.size < 2 or not np.all(np.diff(time_s) > 0):
        raise ValueError(f"{path} time column must contain at least two increasing samples")
    return time_s, {tile: np.asarray(data[channel], dtype=float) for tile, channel in channels.items()}


def rising_edges(
    time_s: np.ndarray,
    voltage_v: np.ndarray,
    threshold_v: float,
    min_separation_s: float,
) -> np.ndarray:
    """Return linearly interpolated low-to-high threshold crossings."""

    time_s = np.asarray(time_s, dtype=float)
    voltage_v = np.asarray(voltage_v, dtype=float)
    crossings = np.flatnonzero(
        (voltage_v[:-1] < threshold_v) & (voltage_v[1:] >= threshold_v)
    )
    edges: list[float] = []
    for index in crossings:
        left, right = voltage_v[index], voltage_v[index + 1]
        fraction = (threshold_v - left) / (right - left)
        edge_s = float(time_s[index] + fraction * (time_s[index + 1] - time_s[index]))
        if not edges or edge_s - edges[-1] >= min_separation_s:
            edges.append(edge_s)
    return np.asarray(edges, dtype=float)


def build_edge_rows(
    inputs: list[Path],
    *,
    time_column: str,
    channels: dict[str, str],
    threshold_v: float,
    min_separation_s: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []
    sequence = 0
    for path in inputs:
        time_s, waveforms = load_scope_csv(path, time_column, channels)
        edges = {
            tile: rising_edges(time_s, waveforms[tile], threshold_v, min_separation_s)
            for tile in TILES
        }
        count = min(edge.size for edge in edges.values())
        if len({edge.size for edge in edges.values()}) != 1:
            mismatches.append(
                {"input": str(path), "complete_edges": count, **{tile: edge.size for tile, edge in edges.items()}}
            )
        for edge_index in range(count):
            reference_s = float(edges["T05"][edge_index])
            values = {tile: float(edges[tile][edge_index]) for tile in TILES}
            offsets_us = {
                tile: (values[tile] - reference_s) * 1e6 for tile in TILES if tile != "T05"
            }
            rows.append(
                {
                    "sequence": sequence,
                    "input": str(path),
                    "edge_in_input": edge_index,
                    **{f"{tile}_edge_s": values[tile] for tile in TILES},
                    **{f"{tile}_minus_T05_us": offsets_us[tile] for tile in offsets_us},
                    "peak_to_peak_skew_us": (max(values.values()) - min(values.values())) * 1e6,
                }
            )
            sequence += 1
    if not rows:
        raise ValueError("no complete four-channel rising-edge sets were found")
    return rows, mismatches


def percentile(values: np.ndarray, percent: float) -> float:
    return float(np.percentile(values, percent)) if values.size else math.nan


def summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for tile in TILES[1:]:
        offsets = np.asarray([row[f"{tile}_minus_T05_us"] for row in rows], dtype=float)
        result.append(
            {
                "kind": "offset_from_T05",
                "tile": tile,
                "count": offsets.size,
                "mean_us": float(np.mean(offsets)),
                "std_us": float(np.std(offsets, ddof=1)) if offsets.size > 1 else 0.0,
                "p50_us": percentile(offsets, 50),
                "p95_abs_us": percentile(np.abs(offsets), 95),
                "min_us": float(np.min(offsets)),
                "max_us": float(np.max(offsets)),
            }
        )
    skew = np.asarray([row["peak_to_peak_skew_us"] for row in rows], dtype=float)
    result.append(
        {
            "kind": "four_tile_peak_to_peak_skew",
            "tile": "T05-T08",
            "count": skew.size,
            "mean_us": float(np.mean(skew)),
            "std_us": float(np.std(skew, ddof=1)) if skew.size > 1 else 0.0,
            "p50_us": percentile(skew, 50),
            "p95_abs_us": percentile(skew, 95),
            "min_us": float(np.min(skew)),
            "max_us": float(np.max(skew)),
        }
    )
    return result


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def create_figures(rows: list[dict[str, Any]], output_prefix: Path) -> list[Path]:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        raise RuntimeError("Matplotlib is required for figures; use --no-figures to skip") from exc

    sequence = np.asarray([row["sequence"] for row in rows], dtype=int)
    offsets_path = output_prefix.with_name(output_prefix.name + "_edge_offsets.png")
    figure, axis = plt.subplots(figsize=(10, 5))
    for tile in TILES[1:]:
        axis.plot(
            sequence,
            [row[f"{tile}_minus_T05_us"] for row in rows],
            ".",
            label=f"{tile} − T05",
        )
    axis.axhline(0.0, color="black", linewidth=0.8)
    axis.set_xlabel("GPIO pulse sequence")
    axis.set_ylabel("scope rising-edge offset (µs)")
    axis.set_title("ZMQ message-arrival GPIO offsets")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.savefig(offsets_path, dpi=180, bbox_inches="tight")
    plt.close(figure)

    skew_path = output_prefix.with_name(output_prefix.name + "_four_tile_skew.png")
    figure, axis = plt.subplots(figsize=(10, 5))
    axis.plot(sequence, [row["peak_to_peak_skew_us"] for row in rows], ".")
    axis.set_xlabel("GPIO pulse sequence")
    axis.set_ylabel("max edge − min edge (µs)")
    axis.set_title("ZMQ four-tile GPIO reception skew")
    axis.grid(alpha=0.25)
    figure.savefig(skew_path, dpi=180, bbox_inches="tight")
    plt.close(figure)
    return [offsets_path, skew_path]


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    validate_config(config)
    threshold = (
        float(config["scope_threshold_v"])
        if args.threshold_v is None
        else args.threshold_v
    )
    separation = (
        float(config["scope_min_edge_separation_s"])
        if args.min_edge_separation_s is None
        else args.min_edge_separation_s
    )
    if threshold <= 0 or separation <= 0:
        raise ValueError("threshold and minimum edge separation must be positive")
    rows, mismatches = build_edge_rows(
        args.inputs,
        time_column=args.time_column,
        channels={tile: str(channel) for tile, channel in config["scope_channel"].items()},
        threshold_v=threshold,
        min_separation_s=separation,
    )
    edge_fields = [
        "sequence",
        "input",
        "edge_in_input",
        *[f"{tile}_edge_s" for tile in TILES],
        *[f"{tile}_minus_T05_us" for tile in TILES[1:]],
        "peak_to_peak_skew_us",
    ]
    edges_path = args.output_prefix.with_name(args.output_prefix.name + "_edges.csv")
    summary_path = args.output_prefix.with_name(args.output_prefix.name + "_summary.csv")
    write_csv(edges_path, rows, edge_fields)
    write_csv(
        summary_path,
        summary_rows(rows),
        ["kind", "tile", "count", "mean_us", "std_us", "p50_us", "p95_abs_us", "min_us", "max_us"],
    )
    outputs = [edges_path, summary_path]
    if mismatches:
        mismatch_path = args.output_prefix.with_name(args.output_prefix.name + "_edge_count_mismatches.csv")
        write_csv(
            mismatch_path,
            mismatches,
            ["input", "complete_edges", *TILES],
        )
        outputs.append(mismatch_path)
    if not args.no_figures:
        outputs.extend(create_figures(rows, args.output_prefix))
    for output in outputs:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
