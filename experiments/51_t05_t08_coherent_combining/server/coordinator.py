#!/usr/bin/env python3
"""Coordinate calibrated, zero-phase, and random-phase 1--4 TX power runs."""

from __future__ import annotations

import argparse
import json
import math
import random
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

import numpy as np


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
EXPERIMENTS_DIR = EXPERIMENT_DIR.parent
sys.path.insert(0, str(EXPERIMENTS_DIR))

from t05_t08_common.config import (
    TESTBENCH_TILES,
    load_config,
    validate_common_config,
)
from t05_t08_common.phase import beamforming_correction, wrap_phase
from t05_t08_common.protocol import receive_json, send_json, socket_streams
from t05_t08_common.results import append_jsonl, utc_now
from t05_t08_common.scope import capture_scope_phase_power


Peer = tuple[socket.socket, TextIO, TextIO]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=EXPERIMENT_DIR / "config.yml")
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--repetitions", type=int)
    parser.add_argument("--scope-resource")
    parser.add_argument(
        "--manual-power",
        action="store_true",
        help="prompt for measured dBm instead of reading a scope",
    )
    parser.add_argument("--no-rewire-prompt", action="store_true")
    parser.add_argument("--allow-uncalibrated-cables", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def default_output() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return EXPERIMENT_DIR / "runs" / f"{stamp}-coherent-combining.jsonl"


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
        results[tile] = result
    return results


def read_power(config: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    if args.manual_power:
        value = float(input("Measured combiner-output power [dBm]: "))
        phase_text = input(
            "Signal minus RF-reference phase [degrees, blank if unavailable]: "
        ).strip()
        result: dict[str, Any] = {"power_dbm": value, "source": "manual"}
        if phase_text:
            result["signal_minus_reference_phase_deg"] = float(phase_text)
            result["signal_minus_reference_phase_rad"] = math.radians(float(phase_text))
        return result
    resource = args.scope_resource or config.get("scope_resource")
    if not resource:
        raise ValueError("set scope_resource or pass --manual-power")
    measured = capture_scope_phase_power(
        str(resource),
        signal_channel=str(config["scope_channel"]),
        reference_channel=str(config["scope_reference_channel"]),
        rf_frequency_hz=float(config["scope_rf_frequency_hz"]),
        points=int(config["scope_points"]),
        timeout_ms=int(config["scope_timeout_ms"]),
    ).to_dict()
    measured["source"] = "scope"
    measured["power_at_combiner_dbm"] = measured["power_dbm"] + float(
        config["combiner_output_attenuation_db"]
    )
    return measured


def execute_power_case(
    peers: dict[str, Peer],
    config: dict[str, Any],
    args: argparse.Namespace,
    active: set[str],
    phases: dict[str, float],
) -> dict[str, Any]:
    """Schedule one common-time TX window and measure during that window."""

    times = command_all(peers, {"command": "get_time"})
    latest_time = max(float(result["device_time_s"]) for result in times.values())
    start_time = math.ceil(latest_time) + 2.0
    command = {
        "command": "transmit",
        "duration_s": float(config["transmit_time_s"]),
        "start_time_s": start_time,
    }
    for tile in TESTBENCH_TILES:
        send_json(
            peers[tile][2],
            {
                **command,
                "active": tile in active,
                "phase_rad": phases[tile],
            },
        )
    wait_s = max(
        0.0,
        start_time - latest_time + float(config["scope_delay_after_tx_start_s"]),
    )
    time.sleep(wait_s)
    power = read_power(config, args)
    for tile in TESTBENCH_TILES:
        result = receive_json(peers[tile][1])
        if result.get("status") != "ok":
            raise RuntimeError(f"{tile} TX failed: {result.get('error')}")
    return power


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    validate_common_config(config)
    if config.get("reference_input_power_dbm") is None:
        print("warning: reference_input_power_dbm is not filled in", file=sys.stderr)
    if config.get("pilot_input_power_dbm") is None:
        print("warning: pilot_input_power_dbm is not filled in", file=sys.stderr)
    repetitions = args.repetitions or int(config["repetitions"])
    if repetitions <= 0:
        raise ValueError("repetitions must be positive")
    if not config.get("reference_cable_phase_calibrated") and not args.allow_uncalibrated_cables:
        raise ValueError(
            "reference cable phases are placeholders; calibrate them or explicitly pass "
            "--allow-uncalibrated-cables for a diagnostic run"
        )
    host = args.host or str(config["control_host"])
    port = args.port or int(config["control_port"])
    output = args.output or default_output()
    modes = ("calibrated", "zero_phase", "random_phase")
    plan = {
        "experiment": config["experiment"],
        "rf_source_tile": str(config["rf_source_tile"]),
        "rf_source_hz": float(config["center_frequency_hz"])
        + float(config["tone_frequency_hz"]),
        "host": host,
        "port": port,
        "tiles": list(TESTBENCH_TILES),
        "modes": list(modes),
        "transmitter_counts": [1, 2, 3, 4],
        "repetitions": repetitions,
        "individual_measurement_repetitions": int(
            config["individual_measurement_repetitions"]
        ),
        "output": str(output),
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
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(len(TESTBENCH_TILES))
    peers: dict[str, Peer] = {}
    try:
        print(f"waiting for T05--T08 on {host}:{port}")
        peers = accept_tiles(server, float(config["socket_timeout_s"]))
        synchronized = command_all(peers, {"command": "synchronize_time"})
        synchronized_times = [
            float(synchronized[tile]["device_time_s"]) for tile in TESTBENCH_TILES
        ]
        time_spread = max(synchronized_times) - min(synchronized_times)
        if time_spread > float(config["time_sync_tolerance_s"]):
            raise RuntimeError(
                f"device-time spread is {time_spread:.6f} s after PPS synchronization"
            )
        append_jsonl(
            output,
            {
                "type": "time_sync",
                "timestamp_utc": utc_now(),
                "device_time_s": {
                    tile: synchronized[tile]["device_time_s"] for tile in TESTBENCH_TILES
                },
                "spread_s": time_spread,
            },
        )
        hardware = command_all(peers, {"command": "get_metadata"})
        for tile in TESTBENCH_TILES:
            append_jsonl(
                output,
                {
                    "type": "hardware",
                    "timestamp_utc": utc_now(),
                    **hardware[tile]["hardware"],
                },
            )
        pilot = command_all(peers, {"command": "capture_pilot"})
        if not args.no_rewire_prompt:
            input(
                "Disconnect and terminate the T04 pilot branch before internal "
                "loopback. Do not move the four tile cables. Press Enter: "
            )
        loopback = command_all(peers, {"command": "capture_loopback"})

        cable_phases = config["reference_cable_phase_deg"]
        calibrated: dict[str, float] = {}
        for tile in TESTBENCH_TILES:
            calibrated[tile] = beamforming_correction(
                float(pilot[tile]["phase"]["phase_rad"]),
                float(loopback[tile]["phase"]["phase_rad"]),
                float(np.deg2rad(cable_phases[tile])),
            )
            append_jsonl(
                output,
                {
                    "type": "calibration",
                    "timestamp_utc": utc_now(),
                    "tile": tile,
                    "reference_minus_pilot": pilot[tile]["phase"],
                    "reference_minus_loopback": loopback[tile]["phase"],
                    "reference_cable_phase_deg": cable_phases[tile],
                    "correction_rad": calibrated[tile],
                    "correction_deg": math.degrees(calibrated[tile]),
                },
            )

        if not args.no_rewire_prompt:
            input(
                "Move the splitter/combiner common port from the T04 pilot branch to the "
                "attenuated scope input, without moving the four tile cables. Press Enter: "
            )

        rng = random.Random(int(config["random_seed"]))
        for repetition in range(int(config["individual_measurement_repetitions"])):
            for tile in TESTBENCH_TILES:
                power = execute_power_case(
                    peers,
                    config,
                    args,
                    {tile},
                    calibrated,
                )
                append_jsonl(
                    output,
                    {
                        "type": "individual_power",
                        "timestamp_utc": utc_now(),
                        "repetition": repetition,
                        "tile": tile,
                        "phase_rad": calibrated[tile],
                        **power,
                    },
                )
                print("individual", repetition, tile, power["power_dbm"], "dBm")

        for repetition in range(repetitions):
            random_phases = {
                tile: rng.uniform(-math.pi, math.pi) for tile in TESTBENCH_TILES
            }
            phase_sets = {
                "calibrated": calibrated,
                "zero_phase": {tile: 0.0 for tile in TESTBENCH_TILES},
                "random_phase": {
                    tile: wrap_phase(calibrated[tile] + random_phases[tile])
                    for tile in TESTBENCH_TILES
                },
            }
            for mode in modes:
                for transmitter_count in range(1, len(TESTBENCH_TILES) + 1):
                    active = set(TESTBENCH_TILES[:transmitter_count])
                    power = execute_power_case(
                        peers,
                        config,
                        args,
                        active,
                        phase_sets[mode],
                    )
                    append_jsonl(
                        output,
                        {
                            "type": "power_measurement",
                            "timestamp_utc": utc_now(),
                            "repetition": repetition,
                            "mode": mode,
                            "transmitter_count": transmitter_count,
                            "active_tiles": sorted(active),
                            "phase_rad": {
                                tile: phase_sets[mode][tile] for tile in sorted(active)
                            },
                            **power,
                        },
                    )
                    print(mode, transmitter_count, power["power_dbm"], "dBm")
    finally:
        for tile, (connection, reader, writer) in peers.items():
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
