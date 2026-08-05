"""Configuration loading and validation shared by the testbench experiments."""

from __future__ import annotations

import re
import socket
from pathlib import Path
from typing import Any

import yaml


TESTBENCH_TILES = ("T05", "T06", "T07", "T08")
_TILE_PATTERN = re.compile(r"(?:^|[-_])(T0[5-8])(?:$|[-_])", re.IGNORECASE)


def load_config(path: str | Path) -> dict[str, Any]:
    """Load a YAML mapping and fail with a useful error for malformed files."""

    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict):
        raise ValueError(f"{config_path} must contain a YAML mapping")
    return data


def resolve_tile(explicit: str | None = None, hostname: str | None = None) -> str:
    """Resolve a canonical T05--T08 identifier from a CLI value or hostname."""

    candidate = explicit or hostname or socket.gethostname()
    candidate_upper = candidate.upper()
    if candidate_upper in TESTBENCH_TILES:
        return candidate_upper
    match = _TILE_PATTERN.search(candidate_upper)
    if match:
        return match.group(1).upper()
    raise ValueError(
        f"Cannot derive a T05--T08 tile from {candidate!r}; pass --tile explicitly"
    )


def validate_common_config(config: dict[str, Any]) -> None:
    """Validate fields needed by every hardware-facing experiment."""

    required = {
        "tiles",
        "rf_source_tile",
        "rf_source_tx_channel",
        "rf_source_tx_antenna",
        "rf_source_tone_amplitude",
        "center_frequency_hz",
        "tone_frequency_hz",
        "sample_rate_hz",
        "master_clock_rate_hz",
        "rf_bandwidth_hz",
        "clock_source",
        "time_source",
    }
    missing = sorted(required.difference(config))
    if missing:
        raise ValueError(f"Missing required configuration keys: {', '.join(missing)}")

    tiles = tuple(str(tile).upper() for tile in config["tiles"])
    if tiles != TESTBENCH_TILES:
        raise ValueError(
            "tiles must be ordered exactly as T05, T06, T07, T08 for this testbench"
        )
    if str(config["rf_source_tile"]).upper() != "T04":
        raise ValueError("rf_source_tile must be T04 for the 5X testbench experiments")
    if int(config["rf_source_tx_channel"]) < 0:
        raise ValueError("rf_source_tx_channel cannot be negative")
    if not isinstance(config["rf_source_tx_antenna"], str) or not config[
        "rf_source_tx_antenna"
    ]:
        raise ValueError("rf_source_tx_antenna must be a non-empty string")
    source_amplitude = float(config["rf_source_tone_amplitude"])
    if not 0 < source_amplitude <= 1:
        raise ValueError("rf_source_tone_amplitude must be in the interval (0, 1]")

    positive_fields = (
        "center_frequency_hz",
        "sample_rate_hz",
        "master_clock_rate_hz",
        "rf_bandwidth_hz",
    )
    for field in positive_fields:
        if float(config[field]) <= 0:
            raise ValueError(f"{field} must be positive")

    sample_rate = float(config["sample_rate_hz"])
    tone_frequency = abs(float(config["tone_frequency_hz"]))
    if tone_frequency >= sample_rate / 2:
        raise ValueError("tone_frequency_hz must lie inside the sampled Nyquist band")

    master_clock = float(config["master_clock_rate_hz"])
    ratio = master_clock / sample_rate
    if not ratio.is_integer():
        raise ValueError("master_clock_rate_hz must be an integer multiple of sample_rate_hz")

    for source in ("clock_source", "time_source"):
        if not isinstance(config[source], str) or not config[source]:
            raise ValueError(f"{source} must be a non-empty string")


def tile_value(config: dict[str, Any], key: str, tile: str, default: Any = None) -> Any:
    """Return a scalar config value or a tile-specific value from a mapping."""

    value = config.get(key, default)
    if isinstance(value, dict):
        if tile not in value:
            raise ValueError(f"{key} has no value for {tile}")
        return value[tile]
    return value
