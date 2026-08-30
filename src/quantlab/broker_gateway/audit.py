"""Append-only broker-gateway audit. Credentials never recorded."""

from __future__ import annotations

from threading import Lock
from typing import Any

_LOCK = Lock()
_LOG: list[dict[str, Any]] = []


def reset_for_tests() -> None:
    with _LOCK:
        _LOG.clear()


def record(event: dict[str, Any]) -> None:
    payload = dict(event)
    for key in list(payload):
        lowered = key.lower()
        if any(token in lowered for token in ("secret", "token", "password", "api_key")):
            payload[key] = "***REDACTED***"
    with _LOCK:
        _LOG.append(payload)


def history() -> list[dict[str, Any]]:
    with _LOCK:
        return list(_LOG)
