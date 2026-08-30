"""Append-only twin audit. Not a broker blotter."""

from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock
from typing import Any

_LOCK = Lock()
_ROWS: list[dict[str, Any]] = []


def reset_for_tests() -> None:
    with _LOCK:
        _ROWS.clear()


def append(event: str, **fields: Any) -> dict[str, Any]:
    row = {
        "event": event,
        "at": datetime.now(tz=UTC).isoformat(),
        "live_trading": False,
        "write_enabled": False,
        **fields,
    }
    with _LOCK:
        _ROWS.append(row)
        return row


def rows() -> list[dict[str, Any]]:
    with _LOCK:
        return list(_ROWS)
