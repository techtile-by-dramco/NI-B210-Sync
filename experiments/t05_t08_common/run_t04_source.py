#!/usr/bin/env python3
"""Transmit the common continuous-wave RF source from T04 for experiments 50--52."""

from __future__ import annotations

import argparse
import json
import math
import socket
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np


EXPERIMENTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXPERIMENTS_DIR))

from t05_t08_common.config import load_config, validate_common_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--tx-gain-db",
        type=float,
        help="T04 TX gain; required for hardware unless set in the YAML",
    )
    parser.add_argument("--amplitude", type=float, help="complex tone amplitude (0, 1]")
    parser.add_argument("--duration", type=float, help="seconds; omit to run until Ctrl-C")
    parser.add_argument(
        "--allow-hostname-mismatch",
        action="store_true",
        help="allow execution when the host name does not contain T04",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def source_plan(config: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    gain = args.tx_gain_db
    if gain is None:
        configured = config.get("rf_source_tx_gain_db")
        gain = None if configured is None else float(configured)
    amplitude = (
        float(args.amplitude)
        if args.amplitude is not None
        else float(config["rf_source_tone_amplitude"])
    )
    if not 0 < amplitude <= 1:
        raise ValueError("source amplitude must be in the interval (0, 1]")
    duration = args.duration
    if duration is not None and duration <= 0:
        raise ValueError("--duration must be positive")
    center = float(config["center_frequency_hz"])
    tone = float(config["tone_frequency_hz"])
    return {
        "experiment": config["experiment"],
        "source_tile": "T04",
        "device_args": str(config.get("rf_source_device_args", "type=b200")),
        "tx_channel": int(config["rf_source_tx_channel"]),
        "tx_antenna": str(config["rf_source_tx_antenna"]),
        "center_frequency_hz": center,
        "tone_frequency_hz": tone,
        "rf_output_frequency_hz": center + tone,
        "sample_rate_hz": float(
            config.get("rf_source_sample_rate_hz", config["sample_rate_hz"])
        ),
        "master_clock_rate_hz": float(config["master_clock_rate_hz"]),
        "rf_bandwidth_hz": float(
            config.get("rf_source_bandwidth_hz", config["rf_bandwidth_hz"])
        ),
        "clock_source": str(config["clock_source"]),
        "time_source": str(config["time_source"]),
        "tx_gain_db": gain,
        "tone_amplitude": amplitude,
        "output_attenuation_db": config.get("rf_source_output_attenuation_db"),
        "duration_s": duration,
    }


def sensor_bool(sensor: Any) -> bool:
    return bool(sensor.to_bool() if hasattr(sensor, "to_bool") else sensor)


def wait_for_lock(getter: Any, timeout_s: float, description: str) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if sensor_bool(getter()):
            return
        time.sleep(0.01)
    raise RuntimeError(f"T04 {description} did not lock within {timeout_s} s")


def run_source(config: dict[str, Any], plan: dict[str, Any]) -> None:
    try:
        import uhd  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError("run this command on T04 with the UHD Python bindings") from exc

    usrp = uhd.usrp.MultiUSRP(plan["device_args"])
    channel = int(plan["tx_channel"])
    usrp.set_master_clock_rate(plan["master_clock_rate_hz"])
    usrp.set_clock_source(plan["clock_source"])
    usrp.set_time_source(plan["time_source"])
    timeout_s = float(config.get("lock_timeout_s", 5.0))
    wait_for_lock(
        lambda: usrp.get_mboard_sensor("ref_locked", 0), timeout_s, "reference"
    )

    usrp.set_tx_rate(plan["sample_rate_hz"], channel)
    usrp.set_tx_bandwidth(plan["rf_bandwidth_hz"], channel)
    usrp.set_tx_gain(float(plan["tx_gain_db"]), channel)
    usrp.set_tx_antenna(plan["tx_antenna"], channel)
    tune_request = uhd.types.TuneRequest(plan["center_frequency_hz"])
    tune_request.args = uhd.types.DeviceAddr("mode_n=integer")
    usrp.set_tx_freq(tune_request, channel)
    try:
        wait_for_lock(
            lambda: usrp.get_tx_sensor("lo_locked", channel), timeout_s, "TX LO"
        )
    except TypeError:
        wait_for_lock(lambda: usrp.get_tx_sensor("lo_locked"), timeout_s, "TX LO")

    usrp.set_time_unknown_pps(uhd.types.TimeSpec(0.0))
    time.sleep(float(config.get("pps_settle_s", 2.0)))
    stream_args = uhd.usrp.StreamArgs("fc32", "sc16")
    stream_args.channels = [channel]
    streamer = usrp.get_tx_stream(stream_args)

    metadata = uhd.types.TXMetadata()
    metadata.has_time_spec = True
    metadata.time_spec = uhd.types.TimeSpec(
        usrp.get_time_now().get_real_secs() + float(config.get("stream_lead_s", 0.5))
    )
    metadata.start_of_burst = True
    metadata.end_of_burst = False
    sample_rate = float(plan["sample_rate_hz"])
    angular_step = 2.0 * math.pi * float(plan["tone_frequency_hz"]) / sample_rate
    chunk_samples = max(1, int(round(sample_rate)))
    indexes = np.arange(chunk_samples, dtype=np.float64)
    phase = 0.0
    started = time.monotonic()
    async_metadata = uhd.types.TXAsyncMetadata()

    print(json.dumps({"type": "t04_source_started", **plan}, sort_keys=True))
    try:
        while plan["duration_s"] is None or time.monotonic() - started < float(
            plan["duration_s"]
        ):
            samples = (
                float(plan["tone_amplitude"])
                * np.exp(1j * (phase + angular_step * indexes))
            ).astype(np.complex64, copy=False).reshape(1, -1)
            phase = math.fmod(phase + angular_step * chunk_samples, 2.0 * math.pi)
            offset = 0
            while offset < chunk_samples:
                sent = streamer.send(samples[:, offset:], metadata, 1.0)
                if sent <= 0:
                    raise RuntimeError("T04 TX send timed out")
                offset += sent
                metadata.has_time_spec = False
                metadata.start_of_burst = False
            while streamer.recv_async_msg(async_metadata, 0.0):
                if async_metadata.event_code != uhd.types.TXMetadataEventCode.burst_ack:
                    raise RuntimeError(
                        f"T04 TX asynchronous error: {async_metadata.event_code}"
                    )
    except KeyboardInterrupt:
        pass
    finally:
        metadata.has_time_spec = False
        metadata.start_of_burst = False
        metadata.end_of_burst = True
        streamer.send(np.zeros((1, 0), dtype=np.complex64), metadata)
        print(json.dumps({"type": "t04_source_stopped"}))


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    validate_common_config(config)
    plan = source_plan(config, args)
    if args.dry_run:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0
    hostname = socket.gethostname().upper()
    if "T04" not in hostname and not args.allow_hostname_mismatch:
        raise RuntimeError(
            f"host {socket.gethostname()!r} is not identifiable as T04; "
            "use T04 or pass --allow-hostname-mismatch after verifying the device"
        )
    if plan["tx_gain_db"] is None:
        raise ValueError(
            "supply --tx-gain-db after measuring the complete T04 distribution path"
        )
    if plan["output_attenuation_db"] is None:
        raise ValueError(
            "fill rf_source_output_attenuation_db after installing and measuring attenuation"
        )
    run_source(config, plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
