"""Ops metrics. Not trading P&L."""

from __future__ import annotations

from threading import Lock

_LOCK = Lock()
_COUNTS: dict[str, int] = {}


def reset_for_tests() -> None:
    with _LOCK:
        _COUNTS.clear()


def incr(name: str) -> int:
    with _LOCK:
        _COUNTS[name] = _COUNTS.get(name, 0) + 1
        return _COUNTS[name]


def snapshot() -> dict[str, int]:
    with _LOCK:
        return dict(_COUNTS)
