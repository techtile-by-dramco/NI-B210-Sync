"""Newline-delimited JSON protocol used by the four-node coordinator."""

from __future__ import annotations

import json
import socket
from typing import Any, TextIO


MAX_MESSAGE_BYTES = 1_000_000


def socket_streams(sock: socket.socket) -> tuple[TextIO, TextIO]:
    return (
        sock.makefile("r", encoding="utf-8", newline="\n"),
        sock.makefile("w", encoding="utf-8", newline="\n"),
    )


def send_json(stream: TextIO, message: dict[str, Any]) -> None:
    encoded = json.dumps(message, sort_keys=True, allow_nan=False)
    if len(encoded.encode("utf-8")) > MAX_MESSAGE_BYTES:
        raise ValueError("protocol message is too large")
    stream.write(encoded + "\n")
    stream.flush()


def receive_json(stream: TextIO) -> dict[str, Any]:
    line = stream.readline(MAX_MESSAGE_BYTES + 1)
    if not line:
        raise ConnectionError("peer closed the control connection")
    if len(line.encode("utf-8")) > MAX_MESSAGE_BYTES:
        raise ValueError("protocol message is too large")
    value = json.loads(line)
    if not isinstance(value, dict):
        raise ValueError("protocol message must be a JSON object")
    return value
