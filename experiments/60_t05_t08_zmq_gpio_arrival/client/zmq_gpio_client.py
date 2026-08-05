#!/usr/bin/env python3
"""Turn a common ZMQ sync message into a one-second Raspberry Pi GPIO pulse."""

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
    parser.add_argument("--tile", required=True, choices=TILES)
    parser.add_argument("--server", required=True, help="reachable Experiment 60 server IP or host")
    parser.add_argument("--repetitions", type=int)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def default_output(tile: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return EXPERIMENT_DIR / "runs" / f"{stamp}-zmq-gpio-{tile}.jsonl"


def endpoint(server: str, port: int) -> str:
    return f"tcp://{server}:{port}"


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    validate_config(config)
    tile = str(args.tile).upper()
    repetitions = (
        int(config["repetitions"]) if args.repetitions is None else args.repetitions
    )
    if repetitions <= 0:
        raise ValueError("repetitions must be positive")
    output = args.output or default_output(tile)
    plan = {
        "experiment": config["experiment"],
        "tile": tile,
        "pub_endpoint": endpoint(args.server, int(config["pub_port"])),
        "ack_endpoint": endpoint(args.server, int(config["ack_port"])),
        "topic": str(config["topic"]),
        "gpio_bcm_pin": int(config["gpio_bcm_pin"][tile]),
        "pulse_duration_s": float(config["pulse_duration_s"]),
        "repetitions": repetitions,
        "output": str(output),
    }
    if args.dry_run:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0

    try:
        import zmq
    except ModuleNotFoundError as exc:
        raise RuntimeError("install pyzmq on the Experiment 60 client") from exc
    try:
        from gpiozero import OutputDevice
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "install gpiozero on this Raspberry Pi before using its GPIO output"
        ) from exc

    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    acknowledgements = context.socket(zmq.PUSH)
    topic = str(config["topic"]).encode("ascii")
    subscriber.setsockopt(zmq.SUBSCRIBE, topic)
    subscriber.connect(plan["pub_endpoint"])
    acknowledgements.connect(plan["ack_endpoint"])
    gpio = OutputDevice(plan["gpio_bcm_pin"], active_high=True, initial_value=False)
    append_jsonl(
        output,
        {"type": "client_start", "timestamp_utc": utc_now(), **plan},
    )
    acknowledgements.send_json(
        {
            "type": "ready",
            "tile": tile,
            "client_ready_monotonic_ns": time.monotonic_ns(),
        }
    )
    expected_sequence = 0
    try:
        while expected_sequence < repetitions:
            if not subscriber.poll(timeout=int(float(config["receive_timeout_s"]) * 1000)):
                raise TimeoutError(
                    f"{tile}: no ZMQ sync message for {config['receive_timeout_s']} s"
                )
            frames = subscriber.recv_multipart()
            if len(frames) != 2 or frames[0] != topic:
                raise ValueError(f"{tile}: malformed ZMQ PUB message")
            received_ns = time.monotonic_ns()
            message = json.loads(frames[1])
            sequence = int(message.get("sequence", -1))
            if message.get("type") != "sync" or sequence != expected_sequence:
                raise RuntimeError(
                    f"{tile}: expected sequence {expected_sequence}, received {message}"
                )

            gpio.on()
            gpio_high_ns = time.monotonic_ns()
            edge = {
                "type": "gpio_rising_edge",
                "tile": tile,
                "sequence": sequence,
                "client_receive_monotonic_ns": received_ns,
                "gpio_high_monotonic_ns": gpio_high_ns,
                "server_publish_monotonic_ns": message.get("server_publish_monotonic_ns"),
            }
            append_jsonl(output, {"timestamp_utc": utc_now(), **edge})
            acknowledgements.send_json(edge)

            time.sleep(float(config["pulse_duration_s"]))
            gpio.off()
            gpio_low_ns = time.monotonic_ns()
            completed = {
                "type": "gpio_pulse_complete",
                "tile": tile,
                "sequence": sequence,
                "gpio_low_monotonic_ns": gpio_low_ns,
                "pulse_duration_monotonic_s": (gpio_low_ns - gpio_high_ns) / 1e9,
            }
            append_jsonl(output, {"timestamp_utc": utc_now(), **completed})
            acknowledgements.send_json(completed)
            expected_sequence += 1
    except Exception as exc:
        append_jsonl(
            output,
            {"type": "client_failure", "timestamp_utc": utc_now(), "error": str(exc)},
        )
        raise
    finally:
        gpio.off()
        gpio.close()
        subscriber.close(linger=0)
        acknowledgements.close(linger=0)
        context.term()
        append_jsonl(output, {"type": "client_end", "timestamp_utc": utc_now()})
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
