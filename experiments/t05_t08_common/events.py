"""Controlled interventions used by state and stability experiments."""

from __future__ import annotations

import gc
import time
from typing import Any, Callable

from .radio import B210Session


AUTOMATED_EVENTS = (
    "fixed_repeat",
    "stream_restart",
    "device_reopen",
    "lo_retune",
    "rx_gain_change",
    "tx_gain_change",
    "rx_port_change",
)
MANUAL_EVENTS = ("cold_start", "reference_interruption")
ALL_EVENTS = AUTOMATED_EVENTS + MANUAL_EVENTS


def reopen_session(
    config: dict[str, Any], tile: str, session: B210Session | None
) -> B210Session:
    if session is not None:
        session.close()
        session = None
        gc.collect()
        time.sleep(float(config.get("event_settle_s", 0.25)))
    return B210Session(config, tile)


def apply_event(
    event: str,
    session: B210Session,
    config: dict[str, Any],
    tile: str,
    *,
    prompt: Callable[[str], None] | None = None,
) -> B210Session:
    """Apply one intervention and return the live session (possibly reopened)."""

    center = float(config["center_frequency_hz"])
    settle = float(config.get("event_settle_s", 0.25))
    if event in ("fixed_repeat", "stream_restart"):
        return session
    if event == "device_reopen":
        return reopen_session(config, tile, session)
    if event == "lo_retune":
        session.timed_tune(center + float(config["retune_offset_hz"]))
        session.timed_tune(center)
    elif event == "rx_gain_change":
        nominal = float(config["measured_rx_gain_db"])
        session.set_measured_rx_gain(nominal + float(config["temporary_rx_gain_delta_db"]))
        time.sleep(settle)
        session.set_measured_rx_gain(nominal)
    elif event == "tx_gain_change":
        nominal = float(config["tx_gain_db"])
        session.set_measured_tx_gain(nominal + float(config["temporary_tx_gain_delta_db"]))
        time.sleep(settle)
        session.set_measured_tx_gain(nominal)
    elif event == "rx_port_change":
        nominal = str(config["measured_rx_antenna"])
        alternate = str(config["alternate_rx_antenna"])
        if nominal == alternate:
            raise ValueError("alternate_rx_antenna must differ from measured_rx_antenna")
        session.usrp.set_rx_antenna(alternate, session.measured_channel)
        time.sleep(settle)
        session.usrp.set_rx_antenna(nominal, session.measured_channel)
    elif event == "cold_start":
        if prompt is None:
            raise RuntimeError("cold_start requires an operator prompt")
        prompt(f"Power-cycle the B210 attached to {tile}.")
        return reopen_session(config, tile, session)
    elif event == "reference_interruption":
        if prompt is None:
            raise RuntimeError("reference_interruption requires an operator prompt")
        prompt(
            f"Disconnect the external 10 MHz reference from {tile}, wait at least one "
            "second, restore it, and wait for the lock indicator."
        )
        session._wait_for_reference_lock(float(config.get("lock_timeout_s", 5.0)))
        session.synchronize_time()
    else:
        raise ValueError(f"unknown event: {event}")
    time.sleep(settle)
    return session
