#!/usr/bin/env python3
"""Coordinate common-device-time Experiment 50 captures across T05--T08."""

from __future__ import annotations

import argparse
import json
import math
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
EXPERIMENTS_DIR = EXPERIMENT_DIR.parent
sys.path.insert(0, str(EXPERIMENTS_DIR))

from t05_t08_common.config import TESTBENCH_TILES, load_config, validate_common_config
from t05_t08_common.protocol import receive_json, send_json, socket_streams
from t05_t08_common.results import append_jsonl, utc_now


Peer = tuple[socket.socket, TextIO, TextIO]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=EXPERIMENT_DIR / "config.yml")
    parser.add_argument(
        "--mode",
        choices=("external_pair", "internal_loopback"),
        help="connection pass; defaults to measurement_mode in the YAML",
    )
    parser.add_argument(
        "--event",
        action="append",
        dest="events",
        help="scheduled event to run; repeat this option for multiple events",
    )
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--host", help="bind address override")
    parser.add_argument("--port", type=int, help="control port override")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def default_output(mode: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return EXPERIMENT_DIR / "runs" / f"{stamp}-{mode}-coordinated.jsonl"


def accept_tiles(server: socket.socket, timeout_s: float) -> dict[str, Peer]:
    peers: dict[str, Peer] = {}
    server.settimeout(timeout_s)
    while len(peers) < len(TESTBENCH_TILES):
        connection, address = server.accept()
        connection.settimeout(timeout_s)
        reader, writer = socket_streams(connection)
        hello = receive_json(reader)
        tile = str(hello.get("tile", "")).upper()
        if hello.get("type") != "hello" or tile not in TESTBENCH_TILES:
            connection.close()
            raise ValueError(f"invalid hello from {address}: {hello}")
        if tile in peers:
            connection.close()
            raise ValueError(f"duplicate connection from {tile}")
        peers[tile] = (connection, reader, writer)
        print(f"connected {tile} from {address[0]}")
    return peers


def command_all(
    peers: dict[str, Peer], command: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    for tile in TESTBENCH_TILES:
        send_json(peers[tile][2], command)
    results: dict[str, dict[str, Any]] = {}
    for tile in TESTBENCH_TILES:
        result = receive_json(peers[tile][1])
        if result.get("status") != "ok":
            raise RuntimeError(f"{tile} failed {command['command']}: {result.get('error')}")
        if result.get("tile") != tile:
            raise RuntimeError(f"expected response from {tile}, received {result.get('tile')}")
        results[tile] = result
    return results


def common_start_time(
    peers: dict[str, Peer], config: dict[str, Any], not_before_s: float = 0.0
) -> float:
    """Choose one future device timestamp after every client has received it."""

    readings = command_all(peers, {"command": "get_time"})
    latest = max(float(result["device_time_s"]) for result in readings.values())
    lead_s = float(config["coordinated_start_lead_s"])
    return float(math.ceil(max(latest + lead_s, not_before_s)))


def capture_all(
    peers: dict[str, Peer],
    config: dict[str, Any],
    *,
    mode: str,
    start_time_s: float,
) -> tuple[dict[str, dict[str, Any]], float]:
    results = command_all(
        peers,
        {"command": "capture", "mode": mode, "start_time_s": start_time_s},
    )
    first_sample = {
        tile: float(results[tile]["first_sample_time_s"]) for tile in TESTBENCH_TILES
    }
    error, spread_s = validate_capture_alignment(
        first_sample, start_time_s, float(config["capture_alignment_tolerance_s"])
    )
    for tile in TESTBENCH_TILES:
        results[tile]["capture_alignment_error_s"] = error[tile]
    return results, spread_s


def validate_capture_alignment(
    first_sample_s: dict[str, float], start_time_s: float, tolerance_s: float
) -> tuple[dict[str, float], float]:
    """Return capture timing errors or reject a non-common device-time capture."""

    if set(first_sample_s) != set(TESTBENCH_TILES):
        raise ValueError("first-sample timestamps are required for exactly T05--T08")
    error = {
        tile: abs(float(value) - float(start_time_s))
        for tile, value in first_sample_s.items()
    }
    spread_s = max(first_sample_s.values()) - min(first_sample_s.values())
    if max(error.values()) > tolerance_s or spread_s > tolerance_s:
        raise RuntimeError(
            "coordinated capture was not aligned: "
            f"requested={start_time_s:.9f}, first_samples={first_sample_s}, "
            f"spread={spread_s:.9f} s, tolerance={tolerance_s:.9f} s"
        )
    return error, spread_s


def append_measurements(
    output: Path,
    results: dict[str, dict[str, Any]],
    *,
    mode: str,
    event: str,
    stage: str,
    repeat: int,
    scheduled_start_time_s: float,
    capture_alignment_spread_s: float,
    event_time_s: float | None,
) -> None:
    for tile in TESTBENCH_TILES:
        result = results[tile]
        append_jsonl(
            output,
            {
                "type": "measurement",
                "timestamp_utc": utc_now(),
                "tile": tile,
                "mode": mode,
                "event": event,
                "stage": stage,
                "repeat": repeat,
                "status": "ok",
                "scheduled_start_time_s": scheduled_start_time_s,
                "event_time_s": event_time_s,
                "first_sample_time_s": result["first_sample_time_s"],
                "capture_alignment_error_s": result["capture_alignment_error_s"],
                "capture_alignment_spread_s": capture_alignment_spread_s,
                "overflow_count": result["overflow_count"],
                "timeout_count": result["timeout_count"],
                "phase": result["phase"],
            },
        )


def main() -> int:
    args = parse_args()
    if args.repeats <= 0:
        raise ValueError("--repeats must be positive")
    config = load_config(args.config)
    validate_common_config(config)
    mode = args.mode or str(config["measurement_mode"])
    available = config["coordinated_events"]
    if not isinstance(available, dict) or mode not in available:
        raise ValueError(f"coordinated_events has no list for mode {mode}")
    events = args.events or list(available[mode])
    unsupported = sorted(set(events).difference(available[mode]))
    if unsupported:
        raise ValueError(
            "events without deterministic common-device-time scheduling: "
            + ", ".join(unsupported)
        )
    host = args.host or str(config["control_host"])
    port = args.port or int(config["control_port"])
    output = args.output or default_output(mode)
    plan = {
        "experiment": config["experiment"],
        "mode": mode,
        "events": events,
        "repeats": args.repeats,
        "host": host,
        "port": port,
        "tiles": list(TESTBENCH_TILES),
        "rf_source_tile": str(config["rf_source_tile"]),
        "rf_source_hz": float(config["center_frequency_hz"])
        + float(config["tone_frequency_hz"]),
        "capture_alignment_tolerance_s": float(config["capture_alignment_tolerance_s"]),
        "output": str(output),
    }
    if args.dry_run:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0

    append_jsonl(
        output,
        {"type": "run_start", "timestamp_utc": utc_now(), **plan, "configuration": config},
    )
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(len(TESTBENCH_TILES))
    peers: dict[str, Peer] = {}
    try:
        print(f"waiting for T05--T08 on {host}:{port}")
        peers = accept_tiles(server, float(config["socket_timeout_s"]))
        synchronized = command_all(peers, {"command": "synchronize_time"})
        append_jsonl(
            output,
            {
                "type": "time_epoch_reset",
                "timestamp_utc": utc_now(),
                "reported_device_time_s": {
                    tile: synchronized[tile]["device_time_s"] for tile in TESTBENCH_TILES
                },
            },
        )
        hardware = command_all(peers, {"command": "get_metadata"})
        for tile in TESTBENCH_TILES:
            append_jsonl(
                output,
                {"type": "hardware", "timestamp_utc": utc_now(), **hardware[tile]["hardware"]},
            )

        for event in events:
            stages = ("after",) if event == "fixed_repeat" else ("before", "after")
            event_time_s: float | None = None
            event_completion_s = 0.0
            for stage in stages:
                if stage == "after" and event not in ("fixed_repeat", "stream_restart"):
                    event_time_s = common_start_time(peers, config)
                    scheduled = command_all(
                        peers,
                        {
                            "command": "schedule_event",
                            "event": event,
                            "event_time_s": event_time_s,
                        },
                    )
                    event_completion_s = max(
                        float(scheduled[tile]["event_completion_time_s"])
                        for tile in TESTBENCH_TILES
                    )
                    append_jsonl(
                        output,
                        {
                            "type": "scheduled_event",
                            "timestamp_utc": utc_now(),
                            "event": event,
                            "event_time_s": event_time_s,
                            "event_completion_time_s": event_completion_s,
                        },
                    )
                for repeat in range(args.repeats):
                    not_before_s = event_completion_s + float(
                        config["coordinated_event_guard_s"]
                    )
                    start_time_s = common_start_time(peers, config, not_before_s)
                    if stage == "after" and event == "stream_restart":
                        event_time_s = start_time_s
                    results, spread_s = capture_all(
                        peers, config, mode=mode, start_time_s=start_time_s
                    )
                    append_measurements(
                        output,
                        results,
                        mode=mode,
                        event=event,
                        stage=stage,
                        repeat=repeat,
                        scheduled_start_time_s=start_time_s,
                        capture_alignment_spread_s=spread_s,
                        event_time_s=event_time_s,
                    )
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
        for _tile, (connection, reader, writer) in peers.items():
            try:
                send_json(writer, {"command": "shutdown"})
                receive_json(reader)
            except Exception:
                pass
            reader.close()
            writer.close()
            connection.close()
        server.close()
        append_jsonl(output, {"type": "run_end", "timestamp_utc": utc_now()})
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
