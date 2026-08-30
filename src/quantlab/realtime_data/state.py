"""Feed connection state. CONNECTED ≠ HEALTHY. Observe-only."""

from __future__ import annotations

from enum import StrEnum
from threading import Lock

from quantlab.realtime_data.errors import InvalidFeedTransition


class FeedState(StrEnum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DEGRADED = "degraded"
    STALE = "stale"
    HALTED = "halted"
    UNKNOWN = "unknown"


LEGAL: frozenset[tuple[FeedState, FeedState]] = frozenset(
    {
        (FeedState.DISCONNECTED, FeedState.CONNECTING),
        (FeedState.CONNECTING, FeedState.CONNECTED),
        (FeedState.CONNECTING, FeedState.DISCONNECTED),
        (FeedState.CONNECTING, FeedState.UNKNOWN),
        (FeedState.CONNECTED, FeedState.DEGRADED),
        (FeedState.CONNECTED, FeedState.STALE),
        (FeedState.CONNECTED, FeedState.HALTED),
        (FeedState.CONNECTED, FeedState.DISCONNECTED),
        (FeedState.DEGRADED, FeedState.CONNECTED),
        (FeedState.DEGRADED, FeedState.STALE),
        (FeedState.DEGRADED, FeedState.DISCONNECTED),
        (FeedState.STALE, FeedState.CONNECTED),
        (FeedState.STALE, FeedState.DISCONNECTED),
        (FeedState.HALTED, FeedState.DISCONNECTED),
        (FeedState.UNKNOWN, FeedState.DISCONNECTED),
        (FeedState.UNKNOWN, FeedState.CONNECTING),
    }
)

_LOCK = Lock()
_STATE = FeedState.DISCONNECTED


def current() -> FeedState:
    return _STATE


def reset_for_tests() -> None:
    global _STATE
    with _LOCK:
        _STATE = FeedState.DISCONNECTED


def force(value: FeedState) -> FeedState:
    global _STATE
    with _LOCK:
        _STATE = value
        return _STATE


def transition(target: FeedState) -> FeedState:
    global _STATE
    with _LOCK:
        if (_STATE, target) not in LEGAL:
            raise InvalidFeedTransition(f"{_STATE.value} → {target.value} is illegal")
        _STATE = target
        return _STATE


def is_healthy(state: FeedState | None = None) -> bool:
    value = state if state is not None else current()
    return value is FeedState.CONNECTED
