#!/usr/bin/env python3
"""Publish common ZMQ sync messages and collect GPIO-edge acknowledgements."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
EXPERIMENTS_DIR = EXPERIMENT_DIR.parent
sys.path.insert(0, str(EXPERIMENT_DIR))
sys.path.insert(0, str(EXPERIMENTS_DIR))

from common import TILES, load_config, validate_config
from t05_t08_common.results import append_jsonl, utc_now


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=EXPERIMENT_DIR / "config.yml")
    parser.add_argument("--host", default="0.0.0.0", help="ZMQ bind address")
    parser.add_argument("--repetitions", type=int)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def default_output() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return EXPERIMENT_DIR / "runs" / f"{stamp}-zmq-gpio-server.jsonl"


def endpoint(host: str, port: int) -> str:
    return f"tcp://{host}:{port}"


def receive_message(socket: Any, timeout_s: float) -> dict[str, Any]:
    if not socket.poll(timeout=int(round(timeout_s * 1000))):
        raise TimeoutError(f"timed out after {timeout_s:g} s waiting for a client message")
    message = socket.recv_json()
    if not isinstance(message, dict):
        raise ValueError("ZMQ client message must be a JSON object")
    return message


def wait_for_ready(socket: Any, timeout_s: float) -> dict[str, dict[str, Any]]:
    ready: dict[str, dict[str, Any]] = {}
    deadline = time.monotonic() + timeout_s
    while len(ready) < len(TILES):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            missing = sorted(set(TILES).difference(ready))
            raise TimeoutError(f"timed out waiting for ready clients: {', '.join(missing)}")
        message = receive_message(socket, remaining)
        tile = str(message.get("tile", "")).upper()
        if message.get("type") != "ready" or tile not in TILES:
            raise ValueError(f"unexpected readiness message: {message}")
        ready[tile] = message
    return ready


def wait_for_trial_acks(
    socket: Any, sequence: int, timeout_s: float
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    edges: dict[str, dict[str, Any]] = {}
    completed: dict[str, dict[str, Any]] = {}
    deadline = time.monotonic() + timeout_s
    while len(completed) < len(TILES):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            missing = sorted(set(TILES).difference(completed))
            raise TimeoutError(
                f"timed out waiting for sequence {sequence} completion: {', '.join(missing)}"
            )
        message = receive_message(socket, remaining)
        tile = str(message.get("tile", "")).upper()
        if tile not in TILES or int(message.get("sequence", -1)) != sequence:
            raise ValueError(f"unexpected trial acknowledgement: {message}")
        if message.get("type") == "gpio_rising_edge":
            edges[tile] = message
        elif message.get("type") == "gpio_pulse_complete":
            completed[tile] = message
        else:
            raise ValueError(f"unexpected trial acknowledgement: {message}")
    missing_edges = sorted(set(TILES).difference(edges))
    if missing_edges:
        raise RuntimeError(
            f"sequence {sequence} completed without rising-edge acknowledgements: "
            + ", ".join(missing_edges)
        )
    return edges, completed


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    validate_config(config)
    repetitions = (
        int(config["repetitions"]) if args.repetitions is None else args.repetitions
    )
    if repetitions <= 0:
        raise ValueError("repetitions must be positive")
    output = args.output or default_output()
    plan = {
        "experiment": config["experiment"],
        "tiles": list(TILES),
        "pub_endpoint": endpoint(args.host, int(config["pub_port"])),
        "ack_endpoint": endpoint(args.host, int(config["ack_port"])),
        "topic": str(config["topic"]),
        "repetitions": repetitions,
        "pulse_duration_s": float(config["pulse_duration_s"]),
        "output": str(output),
    }
    if args.dry_run:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0

    try:
        import zmq
    except ModuleNotFoundError as exc:
        raise RuntimeError("install pyzmq on the Experiment 60 server") from exc

    context = zmq.Context()
    publisher = context.socket(zmq.PUB)
    acknowledgements = context.socket(zmq.PULL)
    publisher.bind(plan["pub_endpoint"])
    acknowledgements.bind(plan["ack_endpoint"])
    append_jsonl(
        output,
        {"type": "run_start", "timestamp_utc": utc_now(), **plan, "configuration": config},
    )
    try:
        ready = wait_for_ready(acknowledgements, float(config["ack_timeout_s"]))
        append_jsonl(
            output,
            {
                "type": "all_clients_ready",
                "timestamp_utc": utc_now(),
                "clients": ready,
            },
        )
        time.sleep(float(config["ready_warmup_s"]))
        topic = str(config["topic"]).encode("ascii")
        for sequence in range(repetitions):
            published_ns = time.monotonic_ns()
            payload = {
                "type": "sync",
                "sequence": sequence,
                "server_publish_monotonic_ns": published_ns,
            }
            publisher.send_multipart([topic, json.dumps(payload, sort_keys=True).encode("utf-8")])
            append_jsonl(
                output,
                {
                    "type": "sync_published",
                    "timestamp_utc": utc_now(),
                    **payload,
                },
            )
            edges, completed = wait_for_trial_acks(
                acknowledgements, sequence, float(config["ack_timeout_s"])
            )
            for tile in TILES:
                append_jsonl(
                    output,
                    {
                        "type": "gpio_rising_edge_ack",
                        "timestamp_utc": utc_now(),
                        "tile": tile,
                        **edges[tile],
                    },
                )
                append_jsonl(
                    output,
                    {
                        "type": "gpio_pulse_complete_ack",
                        "timestamp_utc": utc_now(),
                        "tile": tile,
                        **completed[tile],
                    },
                )
            time.sleep(float(config["inter_trial_s"]))
    except Exception as exc:
        append_jsonl(
            output,
            {"type": "run_failure", "timestamp_utc": utc_now(), "error": str(exc)},
        )
        raise
    finally:
        publisher.close(linger=0)
        acknowledgements.close(linger=0)
        context.term()
        append_jsonl(output, {"type": "run_end", "timestamp_utc": utc_now()})
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
