#!/usr/bin/env python3
"""Run the B210 state/event characterization on one T05--T08 node."""

from __future__ import annotations

import argparse
import json
import logging
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
EXPERIMENTS_DIR = EXPERIMENT_DIR.parent
sys.path.insert(0, str(EXPERIMENTS_DIR))

from t05_t08_common.config import load_config, resolve_tile, validate_common_config
from t05_t08_common.events import MANUAL_EVENTS, apply_event, reopen_session
from t05_t08_common.phase import estimate_relative_phase
from t05_t08_common.protocol import receive_json, send_json, socket_streams
from t05_t08_common.radio import B210Session, RadioError
from t05_t08_common.results import append_jsonl, utc_now


LOGGER = logging.getLogger("state-characterization")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=EXPERIMENT_DIR / "config.yml")
    parser.add_argument("--tile", help="T05, T06, T07, or T08")
    parser.add_argument(
        "--coordinator",
        help="Experiment 50 coordinator hostname or IP; enables coordinated client mode",
    )
    parser.add_argument("--port", type=int, help="coordinator port override")
    parser.add_argument(
        "--mode",
        choices=("external_pair", "internal_loopback"),
        help="override measurement_mode from the YAML file",
    )
    parser.add_argument(
        "--event",
        action="append",
        dest="events",
        help="event to run; repeat this option for multiple events",
    )
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--save-raw-iq", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--allow-manual-events",
        action="store_true",
        help="allow prompts for power/reference interruption",
    )
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


def default_output(tile: str, mode: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return EXPERIMENT_DIR / "runs" / f"{stamp}-{mode}-{tile}.jsonl"


def capture(
    session: B210Session,
    config: dict[str, Any],
    mode: str,
    start_time_s: float | None = None,
):
    duration = float(config["capture_time_s"])
    if mode == "external_pair":
        result = session.capture_pair(duration, start_time_s)
    elif mode == "internal_loopback":
        result = session.capture_internal_loopback(duration, start_time_s)
    else:
        raise ValueError(f"unsupported measurement mode: {mode}")
    discard = int(float(config["discard_time_s"]) * float(config["sample_rate_hz"]))
    estimate = estimate_relative_phase(
        result.samples[0],
        result.samples[1],
        discard_samples=discard,
        block_size=int(config["phase_block_samples"]),
    )
    return result, estimate


def run_coordinated_client(
    args: argparse.Namespace, config: dict[str, Any], tile: str
) -> int:
    """Serve exact-device-time capture and event commands from the coordinator."""

    if not args.coordinator:
        raise ValueError("--coordinator is required for coordinated client mode")
    port = args.port or int(config["control_port"])
    session = B210Session(config, tile)
    try:
        with socket.create_connection(
            (args.coordinator, port), timeout=float(config["socket_timeout_s"])
        ) as connection:
            connection.settimeout(float(config["socket_timeout_s"]))
            reader, writer = socket_streams(connection)
            send_json(writer, {"type": "hello", "tile": tile})
            while True:
                command = receive_json(reader)
                command_name = command.get("command")
                try:
                    if command_name == "capture":
                        mode = str(command["mode"])
                        if mode not in ("external_pair", "internal_loopback"):
                            raise ValueError(f"unsupported coordinated mode: {mode}")
                        captured, estimate = capture(
                            session,
                            config,
                            mode,
                            float(command["start_time_s"]),
                        )
                        result = {
                            "first_sample_time_s": captured.first_sample_time_s,
                            "overflow_count": captured.overflow_count,
                            "timeout_count": captured.timeout_count,
                            "phase": estimate.to_dict(),
                        }
                    elif command_name == "schedule_event":
                        completion = session.schedule_state_event(
                            str(command["event"]), float(command["event_time_s"])
                        )
                        result = {
                            "event_time_s": float(command["event_time_s"]),
                            "event_completion_time_s": completion,
                        }
                    elif command_name == "get_time":
                        result = {
                            "device_time_s": session.usrp.get_time_now().get_real_secs()
                        }
                    elif command_name == "get_metadata":
                        result = {"hardware": session.metadata()}
                    elif command_name == "synchronize_time":
                        session.synchronize_time()
                        result = {
                            "device_time_s": session.usrp.get_time_now().get_real_secs()
                        }
                    elif command_name == "shutdown":
                        send_json(writer, {"type": "result", "tile": tile, "status": "ok"})
                        return 0
                    else:
                        raise ValueError(f"unknown command: {command_name!r}")
                    send_json(
                        writer,
                        {
                            "type": "result",
                            "tile": tile,
                            "command": command_name,
                            "status": "ok",
                            **result,
                        },
                    )
                except Exception as exc:
                    LOGGER.exception("command %s failed", command_name)
                    send_json(
                        writer,
                        {
                            "type": "result",
                            "tile": tile,
                            "command": command_name,
                            "status": "failed",
                            "error": str(exc),
                        },
                    )
                    return 1
    finally:
        session.close()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    if args.repeats <= 0:
        raise ValueError("--repeats must be positive")
    if args.coordinator and not args.mode:
        raise ValueError("coordinated client mode requires --mode")
    config = prepare_config(args.config, args.mode)
    if config.get("reference_input_power_dbm") is None:
        LOGGER.warning("reference_input_power_dbm is not filled in")
    tile = resolve_tile(args.tile)
    mode = str(config["measurement_mode"])
    configured_events = config["automated_events"]
    if not isinstance(configured_events, dict) or mode not in configured_events:
        raise ValueError(f"automated_events has no list for mode {mode}")
    if args.coordinator:
        if args.events:
            raise ValueError("select coordinated events with --event on the server")
        coordinated_events = config.get("coordinated_events")
        if not isinstance(coordinated_events, dict) or mode not in coordinated_events:
            raise ValueError(f"coordinated_events has no list for mode {mode}")
        events = list(coordinated_events[mode])
    else:
        events = args.events or list(configured_events[mode])
    known_events = {
        event for values in configured_events.values() for event in values
    } | set(MANUAL_EVENTS)
    unknown = sorted(set(events).difference(known_events))
    if unknown:
        raise ValueError(f"unknown events: {', '.join(unknown)}")
    if mode == "external_pair" and "tx_gain_change" in events:
        raise ValueError("tx_gain_change requires --mode internal_loopback")
    if (
        set(events).intersection(MANUAL_EVENTS)
        and not args.allow_manual_events
        and not args.dry_run
    ):
        raise ValueError("manual events require --allow-manual-events")
    output = args.output or default_output(tile, mode)

    plan = {
        "experiment": config["experiment"],
        "tile": tile,
        "measurement_mode": mode,
        "events": events,
        "repeats": args.repeats,
        "output": str(output),
        "rf_source_tile": str(config["rf_source_tile"]),
        "rf_source_hz": float(config["center_frequency_hz"])
        + float(config["tone_frequency_hz"]),
        "coordinator": args.coordinator,
        "control_port": args.port or config.get("control_port"),
    }
    if args.dry_run:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0

    if args.coordinator:
        return run_coordinated_client(args, config, tile)

    append_jsonl(
        output,
        {
            "type": "run_start",
            "timestamp_utc": utc_now(),
            **plan,
            "configuration": config,
        },
    )
    session: B210Session | None = None
    failures = 0
    try:
        session = reopen_session(config, tile, None)
        append_jsonl(
            output,
            {"type": "hardware", "timestamp_utc": utc_now(), **session.metadata()},
        )
        for event in events:
            LOGGER.info("%s: event %s", tile, event)
            # A before/after pair makes discrete phase jumps visible. fixed_repeat
            # deliberately has only the repeated after stage.
            stages = ("after",) if event == "fixed_repeat" else ("before", "after")
            for stage in stages:
                if stage == "after":
                    operator_prompt = None
                    if args.allow_manual_events:
                        operator_prompt = lambda message: input(
                            f"\n{message}\nPress Enter when complete: "
                        )
                    session = apply_event(
                        event,
                        session,
                        config,
                        tile,
                        prompt=operator_prompt,
                    )
                for repeat in range(args.repeats):
                    base = {
                        "type": "measurement",
                        "timestamp_utc": utc_now(),
                        "tile": tile,
                        "mode": mode,
                        "event": event,
                        "stage": stage,
                        "repeat": repeat,
                    }
                    try:
                        captured, estimate = capture(session, config, mode)
                        record = {
                            **base,
                            "status": "ok",
                            "first_sample_time_s": captured.first_sample_time_s,
                            "overflow_count": captured.overflow_count,
                            "timeout_count": captured.timeout_count,
                            "phase": estimate.to_dict(),
                        }
                        if args.save_raw_iq:
                            raw_path = output.with_suffix("").with_name(
                                f"{output.stem}-{event}-{stage}-{repeat}.npy"
                            )
                            np.save(raw_path, captured.samples)
                            record["raw_iq"] = str(raw_path)
                    except (RadioError, ValueError) as exc:
                        failures += 1
                        record = {**base, "status": "failed", "error": str(exc)}
                        LOGGER.error("%s %s %s: %s", event, stage, repeat, exc)
                    append_jsonl(output, record)
    except Exception as exc:
        append_jsonl(
            output,
            {
                "type": "run_failure",
                "timestamp_utc": utc_now(),
                "error": str(exc),
            },
        )
        raise
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
    LOGGER.info("results: %s", output)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
