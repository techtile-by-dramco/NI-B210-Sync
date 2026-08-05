"""Configuration helpers for Experiment 60's ZMQ-to-GPIO timing test."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


TILES = ("T05", "T06", "T07", "T08")


def load_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    if not isinstance(config, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return config


def validate_config(config: dict[str, Any]) -> None:
    required = {
        "experiment",
        "tiles",
        "pub_port",
        "ack_port",
        "topic",
        "ready_warmup_s",
        "ack_timeout_s",
        "inter_trial_s",
        "repetitions",
        "pulse_duration_s",
        "receive_timeout_s",
        "gpio_bcm_pin",
        "scope_channel",
        "scope_threshold_v",
        "scope_min_edge_separation_s",
    }
    missing = sorted(required.difference(config))
    if missing:
        raise ValueError(f"missing configuration keys: {', '.join(missing)}")
    if tuple(str(tile).upper() for tile in config["tiles"]) != TILES:
        raise ValueError("tiles must be ordered exactly as T05, T06, T07, T08")
    if int(config["pub_port"]) <= 0 or int(config["ack_port"]) <= 0:
        raise ValueError("ZMQ ports must be positive")
    if int(config["pub_port"]) == int(config["ack_port"]):
        raise ValueError("pub_port and ack_port must differ")
    for key in (
        "ready_warmup_s",
        "ack_timeout_s",
        "inter_trial_s",
        "pulse_duration_s",
        "receive_timeout_s",
        "scope_threshold_v",
        "scope_min_edge_separation_s",
    ):
        if float(config[key]) <= 0:
            raise ValueError(f"{key} must be positive")
    if int(config["repetitions"]) <= 0:
        raise ValueError("repetitions must be positive")
    for key in ("gpio_bcm_pin", "scope_channel"):
        mapping = config[key]
        if not isinstance(mapping, dict) or set(mapping) != set(TILES):
            raise ValueError(f"{key} must contain exactly T05, T06, T07, and T08")
    for tile, pin in config["gpio_bcm_pin"].items():
        if not isinstance(pin, int) or not 0 <= pin <= 27:
            raise ValueError(f"gpio_bcm_pin[{tile}] must be a valid BCM GPIO number")
