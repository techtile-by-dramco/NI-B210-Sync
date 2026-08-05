#!/usr/bin/env python3
"""Summarize and plot Experiment 50 state-characterization measurements."""

from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


EXPERIMENTS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(EXPERIMENTS_DIR))

from t05_t08_common.phase import circular_mean, circular_std, wrap_phase
from t05_t08_common.results import read_jsonl


GroupKey = tuple[str, str, str, str]
RunGroupKey = tuple[str, str, str, str, str]
EVENT_ORDER = (
    "fixed_repeat",
    "stream_restart",
    "device_reopen",
    "lo_retune",
    "rx_gain_change",
    "tx_gain_change",
    "rx_port_change",
    "cold_start",
    "reference_interruption",
)
MODE_ORDER = ("external_pair", "internal_loopback")
TILE_ORDER = ("T05", "T06", "T07", "T08")
STAGE_ORDER = ("before", "after")
SUMMARY_FIELDS = (
    "tile",
    "mode",
    "event",
    "stage",
    "successful_runs",
    "failed_runs",
    "success_fraction",
    "circular_mean_deg",
    "circular_std_deg",
    "jump_from_before_deg",
    "jump_circular_std_deg",
    "paired_event_runs",
    "within_capture_circular_std_mean_deg",
    "within_capture_circular_std_max_deg",
    "amplitude_mean",
    "amplitude_std",
    "residual_rms_mean",
    "residual_rms_std",
    "correlation_quality_mean_db",
    "sample_count_mean",
    "block_count_mean",
    "capture_alignment_error_max_s",
    "capture_alignment_spread_max_s",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=Path("state_summary.csv"))
    parser.add_argument(
        "--figure-dir",
        type=Path,
        help="output directory; defaults to <CSV stem>_figures beside the CSV",
    )
    parser.add_argument(
        "--no-figures",
        action="store_true",
        help="write only the CSV (Matplotlib is not imported)",
    )
    return parser.parse_args()


def _ordered(values: set[str], preferred: tuple[str, ...]) -> list[str]:
    return [value for value in preferred if value in values] + sorted(
        values.difference(preferred)
    )


def _mean(values: list[float]) -> float:
    return float(np.mean(values)) if values else math.nan


def _std(values: list[float]) -> float:
    if len(values) > 1:
        return float(np.std(values, ddof=1))
    return 0.0 if values else math.nan


def _max(values: list[float]) -> float:
    return max(values) if values else math.nan


def load_measurements(
    inputs: list[Path],
) -> tuple[
    dict[GroupKey, list[dict[str, Any]]],
    dict[GroupKey, int],
    dict[tuple[str, str, str], list[float]],
    list[dict[str, Any]],
]:
    """Load measurements and calculate paired event jumps per input run."""

    successful: dict[GroupKey, list[dict[str, Any]]] = defaultdict(list)
    failed: dict[GroupKey, int] = defaultdict(int)
    run_phases: dict[RunGroupKey, list[float]] = defaultdict(list)
    observations: list[dict[str, Any]] = []

    for input_index, path in enumerate(inputs):
        run_id = f"{input_index}:{path.resolve()}"
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
                phase = record.get("phase")
                if not isinstance(phase, dict) or "phase_rad" not in phase:
                    raise ValueError(f"successful measurement in {path} has no phase estimate")
                annotated = {**record, "_run_id": run_id, "_input_path": str(path)}
                successful[key].append(annotated)
                observations.append(annotated)
                run_phases[(run_id, *key)].append(float(phase["phase_rad"]))
            else:
                failed[key] += 1

    run_means = {
        key: circular_mean(np.asarray(phases, dtype=float))
        for key, phases in run_phases.items()
        if phases
    }
    paired_jumps: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    run_events = {
        (run_id, tile, mode, event)
        for run_id, tile, mode, event, _stage in run_means
    }
    for run_id, tile, mode, event in run_events:
        before = run_means.get((run_id, tile, mode, event, "before"))
        after = run_means.get((run_id, tile, mode, event, "after"))
        if before is not None and after is not None:
            paired_jumps[(tile, mode, event)].append(float(wrap_phase(after - before)))

    return successful, failed, paired_jumps, observations


def summarize(
    successful: dict[GroupKey, list[dict[str, Any]]],
    failed: dict[GroupKey, int],
    paired_jumps: dict[tuple[str, str, str], list[float]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in sorted(set(successful) | set(failed)):
        tile, mode, event, stage = key
        records = successful.get(key, [])
        phases = np.asarray(
            [float(record["phase"]["phase_rad"]) for record in records], dtype=float
        )
        phase_mean = circular_mean(phases) if phases.size else math.nan
        phase_std = circular_std(phases) if phases.size else math.nan
        within_stds = [float(record["phase"]["circular_std_rad"]) for record in records]
        amplitudes = [float(record["phase"]["amplitude"]) for record in records]
        residuals = [float(record["phase"]["residual_rms"]) for record in records]
        qualities = [
            20.0
            * math.log10(
                max(amplitude, np.finfo(float).tiny)
                / max(residual, np.finfo(float).tiny)
            )
            for amplitude, residual in zip(amplitudes, residuals)
        ]
        samples = [float(record["phase"]["sample_count"]) for record in records]
        blocks = [float(record["phase"]["block_count"]) for record in records]
        alignment_errors = [
            float(record["capture_alignment_error_s"])
            for record in records
            if record.get("capture_alignment_error_s") is not None
        ]
        alignment_spreads = [
            float(record["capture_alignment_spread_s"])
            for record in records
            if record.get("capture_alignment_spread_s") is not None
        ]
        jumps = paired_jumps.get((tile, mode, event), [])
        jump_mean = circular_mean(np.asarray(jumps)) if jumps else math.nan
        jump_std = circular_std(np.asarray(jumps)) if jumps else math.nan
        failed_count = failed.get(key, 0)
        total = len(records) + failed_count
        rows.append(
            {
                "tile": tile,
                "mode": mode,
                "event": event,
                "stage": stage,
                "successful_runs": len(records),
                "failed_runs": failed_count,
                "success_fraction": len(records) / total if total else math.nan,
                "circular_mean_deg": math.degrees(phase_mean),
                "circular_std_deg": math.degrees(phase_std),
                "jump_from_before_deg": (
                    math.degrees(jump_mean) if stage == "after" else 0.0
                ),
                "jump_circular_std_deg": (
                    math.degrees(jump_std) if stage == "after" else 0.0
                ),
                "paired_event_runs": len(jumps) if stage == "after" else 0,
                "within_capture_circular_std_mean_deg": math.degrees(_mean(within_stds)),
                "within_capture_circular_std_max_deg": (
                    math.degrees(max(within_stds)) if within_stds else math.nan
                ),
                "amplitude_mean": _mean(amplitudes),
                "amplitude_std": _std(amplitudes),
                "residual_rms_mean": _mean(residuals),
                "residual_rms_std": _std(residuals),
                "correlation_quality_mean_db": _mean(qualities),
                "sample_count_mean": _mean(samples),
                "block_count_mean": _mean(blocks),
                "capture_alignment_error_max_s": _max(alignment_errors),
                "capture_alignment_spread_max_s": _max(alignment_spreads),
            }
        )
    return rows


def write_summary(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _load_pyplot():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Matplotlib is required for figures; install the shared requirements "
            "or pass --no-figures"
        ) from exc
    return plt


def _save_figure(figure: Any, path: Path, plt: Any) -> Path:
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)
    return path


def plot_phase_observations(
    observations: list[dict[str, Any]], figure_dir: Path, plt: Any
) -> Path:
    modes = _ordered({str(record["mode"]) for record in observations}, MODE_ORDER)
    figure, axes = plt.subplots(
        max(1, len(modes)),
        1,
        figsize=(max(11, 1.15 * len(EVENT_ORDER)), 4.2 * max(1, len(modes))),
        squeeze=False,
    )
    colors = dict(zip(TILE_ORDER, plt.get_cmap("tab10").colors))
    offsets = dict(zip(TILE_ORDER, np.linspace(-0.24, 0.24, len(TILE_ORDER))))
    for axis, mode in zip(axes[:, 0], modes):
        mode_records = [record for record in observations if record["mode"] == mode]
        pairs = {(str(record["event"]), str(record["stage"])) for record in mode_records}
        events = _ordered({event for event, _stage in pairs}, EVENT_ORDER)
        categories = [
            (event, stage)
            for event in events
            for stage in STAGE_ORDER
            if (event, stage) in pairs
        ]
        category_index = {category: index for index, category in enumerate(categories)}
        for tile in _ordered({str(record["tile"]) for record in mode_records}, TILE_ORDER):
            values = [record for record in mode_records if record["tile"] == tile]
            x_values = [
                category_index[(str(record["event"]), str(record["stage"]))]
                + offsets.get(tile, 0.0)
                for record in values
            ]
            y_values = [math.degrees(float(record["phase"]["phase_rad"])) for record in values]
            axis.scatter(
                x_values,
                y_values,
                s=22,
                alpha=0.55,
                color=colors.get(tile),
                label=tile,
            )
        axis.axhline(0.0, color="0.75", linewidth=0.8)
        axis.set_ylim(-185.0, 185.0)
        axis.set_ylabel("reference − measured phase (deg)")
        axis.set_title(mode.replace("_", " "))
        axis.set_xticks(range(len(categories)))
        axis.set_xticklabels(
            [f"{event.replace('_', ' ')}\n{stage}" for event, stage in categories],
            rotation=35,
            ha="right",
        )
        axis.grid(axis="y", alpha=0.25)
        axis.legend(ncol=min(4, len(TILE_ORDER)), loc="upper right")
    if not modes:
        axes[0, 0].text(
            0.5, 0.5, "No successful measurements", ha="center", va="center"
        )
        axes[0, 0].set_axis_off()
    figure.suptitle("Experiment 50: all successful phase observations", fontsize=14)
    figure.tight_layout()
    return _save_figure(figure, figure_dir / "phase_observations.png", plt)


def plot_event_jumps(rows: list[dict[str, Any]], figure_dir: Path, plt: Any) -> Path:
    jump_rows = [
        row
        for row in rows
        if row["stage"] == "after"
        and int(row["paired_event_runs"]) > 0
        and math.isfinite(float(row["jump_from_before_deg"]))
    ]
    modes = _ordered({str(row["mode"]) for row in jump_rows}, MODE_ORDER)
    figure, axes = plt.subplots(
        max(1, len(modes)), 1, figsize=(11, 4.2 * max(1, len(modes))), squeeze=False
    )
    colors = dict(zip(TILE_ORDER, plt.get_cmap("tab10").colors))
    offsets = dict(zip(TILE_ORDER, np.linspace(-0.24, 0.24, len(TILE_ORDER))))
    for axis, mode in zip(axes[:, 0], modes):
        mode_rows = [row for row in jump_rows if row["mode"] == mode]
        events = _ordered({str(row["event"]) for row in mode_rows}, EVENT_ORDER)
        for tile in _ordered({str(row["tile"]) for row in mode_rows}, TILE_ORDER):
            tile_rows = {str(row["event"]): row for row in mode_rows if row["tile"] == tile}
            present = [event for event in events if event in tile_rows]
            x_values = [events.index(event) + offsets.get(tile, 0.0) for event in present]
            y_values = [float(tile_rows[event]["jump_from_before_deg"]) for event in present]
            y_errors = [float(tile_rows[event]["jump_circular_std_deg"]) for event in present]
            axis.errorbar(
                x_values,
                y_values,
                yerr=y_errors,
                fmt="o",
                capsize=3,
                color=colors.get(tile),
                label=tile,
            )
        axis.axhline(0.0, color="black", linewidth=0.9)
        axis.set_ylabel("after − before phase (deg)")
        axis.set_title(mode.replace("_", " "))
        axis.set_xticks(range(len(events)))
        axis.set_xticklabels([event.replace("_", " ") for event in events], rotation=30, ha="right")
        axis.grid(axis="y", alpha=0.25)
        axis.legend(ncol=min(4, len(TILE_ORDER)), loc="best")
    if not modes:
        axes[0, 0].text(0.5, 0.5, "No paired before/after events", ha="center", va="center")
        axes[0, 0].set_axis_off()
    figure.suptitle("Experiment 50: phase jump caused by each event", fontsize=14)
    figure.tight_layout()
    return _save_figure(figure, figure_dir / "event_phase_jumps.png", plt)


def plot_repeatability_quality(
    rows: list[dict[str, Any]], figure_dir: Path, plt: Any
) -> Path:
    valid_rows = [row for row in rows if int(row["successful_runs"]) > 0]
    modes = _ordered({str(row["mode"]) for row in valid_rows}, MODE_ORDER)
    figure, axes = plt.subplots(
        max(1, len(modes)), 2, figsize=(16, 4.5 * max(1, len(modes))), squeeze=False
    )
    colors = dict(zip(TILE_ORDER, plt.get_cmap("tab10").colors))
    offsets = dict(zip(TILE_ORDER, np.linspace(-0.24, 0.24, len(TILE_ORDER))))
    for row_index, mode in enumerate(modes):
        mode_rows = [row for row in valid_rows if row["mode"] == mode]
        events = _ordered({str(row["event"]) for row in mode_rows}, EVENT_ORDER)
        categories = [
            (event, stage)
            for event in events
            for stage in STAGE_ORDER
            if any(row["event"] == event and row["stage"] == stage for row in mode_rows)
        ]
        for tile in _ordered({str(row["tile"]) for row in mode_rows}, TILE_ORDER):
            tile_rows = {
                (str(row["event"]), str(row["stage"])): row
                for row in mode_rows
                if row["tile"] == tile
            }
            present = [category for category in categories if category in tile_rows]
            x_values = [categories.index(category) + offsets.get(tile, 0.0) for category in present]
            axes[row_index, 0].plot(
                x_values,
                [float(tile_rows[category]["circular_std_deg"]) for category in present],
                "o",
                color=colors.get(tile),
                label=tile,
            )
            axes[row_index, 1].plot(
                x_values,
                [float(tile_rows[category]["correlation_quality_mean_db"]) for category in present],
                "o",
                color=colors.get(tile),
                label=tile,
            )
        labels = [f"{event.replace('_', ' ')}\n{stage}" for event, stage in categories]
        for axis in axes[row_index]:
            axis.set_xticks(range(len(categories)))
            axis.set_xticklabels(labels, rotation=35, ha="right")
            axis.grid(axis="y", alpha=0.25)
            axis.legend(ncol=min(4, len(TILE_ORDER)), loc="best")
        axes[row_index, 0].set_ylabel("between-run circular std (deg)")
        axes[row_index, 1].set_ylabel("correlation amplitude/residual (dB)")
        axes[row_index, 0].set_title(f"{mode.replace('_', ' ')} — repeatability")
        axes[row_index, 1].set_title(f"{mode.replace('_', ' ')} — measurement quality")
    if not modes:
        for axis in axes[0]:
            axis.text(0.5, 0.5, "No successful measurements", ha="center", va="center")
            axis.set_axis_off()
    figure.suptitle("Experiment 50: repeatability and correlation quality", fontsize=14)
    figure.tight_layout()
    return _save_figure(figure, figure_dir / "repeatability_and_quality.png", plt)


def create_figures(
    observations: list[dict[str, Any]], rows: list[dict[str, Any]], figure_dir: Path
) -> list[Path]:
    figure_dir.mkdir(parents=True, exist_ok=True)
    plt = _load_pyplot()
    return [
        plot_phase_observations(observations, figure_dir, plt),
        plot_event_jumps(rows, figure_dir, plt),
        plot_repeatability_quality(rows, figure_dir, plt),
    ]


def main() -> int:
    args = parse_args()
    successful, failed, paired_jumps, observations = load_measurements(args.inputs)
    rows = summarize(successful, failed, paired_jumps)
    write_summary(args.output, rows)
    outputs = [args.output]
    if not args.no_figures:
        figure_dir = args.figure_dir or args.output.with_name(args.output.stem + "_figures")
        outputs.extend(create_figures(observations, rows, figure_dir))
    for output in outputs:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
