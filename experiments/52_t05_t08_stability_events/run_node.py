#!/usr/bin/env python3
"""Track T05--T08 phase over time and around one controlled intervention."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


EXPERIMENT_DIR = Path(__file__).resolve().parent
EXPERIMENTS_DIR = EXPERIMENT_DIR.parent
sys.path.insert(0, str(EXPERIMENTS_DIR))

from t05_t08_common.config import load_config, resolve_tile, validate_common_config
from t05_t08_common.events import ALL_EVENTS, MANUAL_EVENTS, apply_event, reopen_session
from t05_t08_common.phase import estimate_relative_phase
from t05_t08_common.radio import B210Session, RadioError
from t05_t08_common.results import append_jsonl, utc_now


LOGGER = logging.getLogger("stability-events")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=EXPERIMENT_DIR / "config.yml")
    parser.add_argument("--tile")
    parser.add_argument(
        "--mode", choices=("external_pair", "internal_loopback"), help="connection pass"
    )
    parser.add_argument(
        "--event",
        default="fixed_repeat",
        choices=ALL_EVENTS,
        help="single event applied at --event-at (fixed_repeat means steady state)",
    )
    parser.add_argument("--event-at", type=int)
    parser.add_argument("--measurements", type=int)
    parser.add_argument("--interval", type=float)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--save-raw-iq", action="store_true")
    parser.add_argument("--allow-manual-event", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def prepare_config(path: Path, mode: str | None) -> dict[str, Any]:
    config = load_config(path)
    validate_common_config(config)
    if mode:
        config["measurement_mode"] = mode
    if config["measurement_mode"] == "external_pair":
        config["loopback_fpga"] = None
    fpga = config.get("loopback_fpga")
    if fpga and not Path(fpga).is_absolute():
        config["loopback_fpga"] = str((path.resolve().parent / fpga).resolve())
    return config


def default_output(tile: str, mode: str, event: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return EXPERIMENT_DIR / "runs" / f"{stamp}-{mode}-{event}-{tile}.jsonl"


def temperature_c(session: B210Session) -> float | None:
    """Return the first temperature-like sensor UHD exposes, if any."""

    candidates: list[tuple[Any, tuple[Any, ...]]] = []
    try:
        for name in session.usrp.get_mboard_sensor_names(0):
            candidates.append((session.usrp.get_mboard_sensor, (name, 0)))
    except Exception:
        pass
    for channel in session.channels:
        for direction in ("rx", "tx"):
            names = getattr(session.usrp, f"get_{direction}_sensor_names")
            getter = getattr(session.usrp, f"get_{direction}_sensor")
            try:
                for name in names(channel):
                    candidates.append((getter, (name, channel)))
            except Exception:
                pass
    for getter, arguments in candidates:
        if "temp" not in str(arguments[0]).lower():
            continue
        try:
            sensor = getter(*arguments)
            return float(sensor.to_real() if hasattr(sensor, "to_real") else sensor)
        except Exception:
            continue
    return None


def capture(session: B210Session, config: dict[str, Any], mode: str):
    duration = float(config["capture_time_s"])
    captured = (
        session.capture_pair(duration)
        if mode == "external_pair"
        else session.capture_internal_loopback(duration)
    )
    discard = int(float(config["discard_time_s"]) * float(config["sample_rate_hz"]))
    estimate = estimate_relative_phase(
        captured.samples[0],
        captured.samples[1],
        discard_samples=discard,
        block_size=int(config["phase_block_samples"]),
    )
    return captured, estimate


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    config = prepare_config(args.config, args.mode)
    if config.get("reference_input_power_dbm") is None:
        LOGGER.warning("reference_input_power_dbm is not filled in")
    tile = resolve_tile(args.tile)
    mode = str(config["measurement_mode"])
    measurements = args.measurements or int(config["measurements"])
    interval = args.interval if args.interval is not None else float(
        config["measurement_interval_s"]
    )
    event_at = args.event_at if args.event_at is not None else int(
        config["event_at_measurement"]
    )
    if measurements <= 0 or interval < 0:
        raise ValueError("measurements must be positive and interval cannot be negative")
    if args.event != "fixed_repeat" and not 0 < event_at < measurements:
        raise ValueError("event-at must leave at least one measurement before and after")
    if mode == "external_pair" and args.event == "tx_gain_change":
        raise ValueError("tx_gain_change requires --mode internal_loopback")
    if args.event in MANUAL_EVENTS and not args.allow_manual_event and not args.dry_run:
        raise ValueError("manual events require --allow-manual-event")
    output = args.output or default_output(tile, mode, args.event)
    plan = {
        "experiment": config["experiment"],
        "rf_source_tile": str(config["rf_source_tile"]),
        "rf_source_hz": float(config["center_frequency_hz"])
        + float(config["tone_frequency_hz"]),
        "tile": tile,
        "mode": mode,
        "event": args.event,
        "event_at_measurement": event_at,
        "measurements": measurements,
        "interval_s": interval,
        "output": str(output),
        "estimated_duration_s": max(
            max(0, measurements - 1) * interval + float(config["capture_time_s"]),
            measurements * float(config["capture_time_s"]),
        ),
    }
    if args.dry_run:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0

    append_jsonl(
        output,
        {
            "type": "run_start",
            "timestamp_utc": utc_now(),
            **plan,
            "configuration": config,
        },
    )
    session: B210Session | None = reopen_session(config, tile, None)
    append_jsonl(
        output,
        {"type": "hardware", "timestamp_utc": utc_now(), **session.metadata()},
    )
    start = time.monotonic()
    failures = 0
    event_applied = False
    try:
        for index in range(measurements):
            target = start + index * interval
            time.sleep(max(0.0, target - time.monotonic()))
            if args.event != "fixed_repeat" and index == event_at:
                operator_prompt = None
                if args.allow_manual_event:
                    operator_prompt = lambda message: input(
                        f"\n{message}\nPress Enter when complete: "
                    )
                session = apply_event(
                    args.event,
                    session,
                    config,
                    tile,
                    prompt=operator_prompt,
                )
                event_applied = True
                append_jsonl(
                    output,
                    {
                        "type": "event",
                        "timestamp_utc": utc_now(),
                        "elapsed_s": time.monotonic() - start,
                        "tile": tile,
                        "event": args.event,
                        "measurement_index": index,
                    },
                )
            base = {
                "type": "measurement",
                "timestamp_utc": utc_now(),
                "elapsed_s": time.monotonic() - start,
                "tile": tile,
                "mode": mode,
                "event": args.event,
                "event_applied": event_applied,
                "measurement_index": index,
            }
            try:
                captured, estimate = capture(session, config, mode)
                record = {
                    **base,
                    "status": "ok",
                    "temperature_c": temperature_c(session),
                    "first_sample_time_s": captured.first_sample_time_s,
                    "overflow_count": captured.overflow_count,
                    "timeout_count": captured.timeout_count,
                    "phase": estimate.to_dict(),
                }
                if args.save_raw_iq:
                    raw_path = output.with_suffix("").with_name(
                        f"{output.stem}-{index:06d}.npy"
                    )
                    np.save(raw_path, captured.samples)
                    record["raw_iq"] = str(raw_path)
            except (RadioError, ValueError) as exc:
                failures += 1
                LOGGER.error("measurement %d failed: %s", index, exc)
                record = {**base, "status": "failed", "error": str(exc)}
            append_jsonl(output, record)
    finally:
        if session is not None:
            session.close()
        append_jsonl(
            output,
            {
                "type": "run_end",
                "timestamp_utc": utc_now(),
                "failed_measurements": failures,
            },
        )
    print(output)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
