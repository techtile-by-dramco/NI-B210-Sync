#!/usr/bin/env python3
"""Connect one T05--T08 B210 to the coherent-combining coordinator."""

from __future__ import annotations

import argparse
import json
import logging
import socket
import sys
from pathlib import Path
from typing import Any


EXPERIMENT_DIR = Path(__file__).resolve().parent
EXPERIMENTS_DIR = EXPERIMENT_DIR.parent
sys.path.insert(0, str(EXPERIMENTS_DIR))

from t05_t08_common.config import load_config, resolve_tile, validate_common_config
from t05_t08_common.phase import estimate_relative_phase
from t05_t08_common.protocol import receive_json, send_json, socket_streams
from t05_t08_common.radio import B210Session


LOGGER = logging.getLogger("coherent-node")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=EXPERIMENT_DIR / "config.yml")
    parser.add_argument("--tile")
    parser.add_argument("--coordinator", required=True, help="coordinator hostname or IP")
    parser.add_argument("--port", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def prepare_config(path: Path) -> dict[str, Any]:
    config = load_config(path)
    validate_common_config(config)
    fpga = config.get("loopback_fpga")
    if fpga and not Path(fpga).is_absolute():
        config["loopback_fpga"] = str((path.resolve().parent / fpga).resolve())
    return config


def estimate_capture(session: B210Session, config: dict[str, Any], loopback: bool):
    duration = float(config["capture_time_s"])
    captured = (
        session.capture_internal_loopback(duration)
        if loopback
        else session.capture_pair(duration)
    )
    discard = int(float(config["discard_time_s"]) * float(config["sample_rate_hz"]))
    estimate = estimate_relative_phase(
        captured.samples[0],
        captured.samples[1],
        discard_samples=discard,
        block_size=int(config["phase_block_samples"]),
    )
    return {
        "phase": estimate.to_dict(),
        "first_sample_time_s": captured.first_sample_time_s,
        "device_time_s": session.usrp.get_time_now().get_real_secs(),
    }


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    config = prepare_config(args.config)
    tile = resolve_tile(args.tile)
    port = args.port or int(config["control_port"])
    if args.dry_run:
        print(
            json.dumps(
                {
                    "tile": tile,
                    "coordinator": args.coordinator,
                    "port": port,
                    "commands": [
                        "synchronize_time",
                        "get_metadata",
                        "capture_pilot",
                        "capture_loopback",
                        "transmit (repeated)",
                        "shutdown",
                    ],
                },
                indent=2,
            )
        )
        return 0

    session = B210Session(config, tile)
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
                if command_name == "capture_pilot":
                    result = estimate_capture(session, config, loopback=False)
                elif command_name == "capture_loopback":
                    result = estimate_capture(session, config, loopback=True)
                elif command_name == "transmit":
                    active = bool(command["active"])
                    if active:
                        session.transmit(
                            duration_s=float(command["duration_s"]),
                            phase_rad=float(command["phase_rad"]),
                            start_time_s=float(command["start_time_s"]),
                        )
                    result = {
                        "active": active,
                        "device_time_s": session.usrp.get_time_now().get_real_secs(),
                    }
                elif command_name == "get_time":
                    result = {"device_time_s": session.usrp.get_time_now().get_real_secs()}
                elif command_name == "get_metadata":
                    result = {"hardware": session.metadata()}
                elif command_name == "synchronize_time":
                    session.synchronize_time()
                    result = {"device_time_s": session.usrp.get_time_now().get_real_secs()}
                elif command_name == "shutdown":
                    send_json(writer, {"type": "result", "tile": tile, "status": "ok"})
                    break
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
