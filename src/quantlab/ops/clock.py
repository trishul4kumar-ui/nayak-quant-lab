"""Clock integrity. Rollback and future timestamps fail closed."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from threading import Lock

from quantlab.ops.errors import ClockError

_LOCK = Lock()
_LAST = datetime(2024, 1, 2, tzinfo=UTC)
_MAX_FUTURE = timedelta(minutes=5)


def reset_for_tests() -> None:
    global _LAST
    with _LOCK:
        _LAST = datetime(2024, 1, 2, tzinfo=UTC)


def last_seen() -> datetime:
    return _LAST


def observe(now: datetime) -> datetime:
    global _LAST
    if now.tzinfo is None:
        raise ClockError("naive timestamps are rejected")
    with _LOCK:
        if now < _LAST:
            raise ClockError("clock rollback detected")
        too_future = now > _LAST + _MAX_FUTURE and now.year > 2100
        if too_future:
            raise ClockError("future timestamp rejected")
        _LAST = now
        return _LAST
