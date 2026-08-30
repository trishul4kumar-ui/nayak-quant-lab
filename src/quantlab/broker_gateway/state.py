"""Read-only broker connection state. BROKER_CONNECTED ≠ TRADING_AUTHORIZED."""

from __future__ import annotations

from enum import StrEnum
from threading import Lock

from quantlab.broker_gateway.errors import InvalidBrokerTransition


class ConnectionState(StrEnum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED_READ_ONLY = "connected_read_only"
    DEGRADED = "degraded"
    STALE = "stale"
    RECONCILIATION_REQUIRED = "reconciliation_required"
    BLOCKED = "blocked"


LEGAL: frozenset[tuple[ConnectionState, ConnectionState]] = frozenset(
    {
        (ConnectionState.DISCONNECTED, ConnectionState.CONNECTING),
        (ConnectionState.CONNECTING, ConnectionState.CONNECTED_READ_ONLY),
        (ConnectionState.CONNECTING, ConnectionState.BLOCKED),
        (ConnectionState.CONNECTING, ConnectionState.DEGRADED),
        (ConnectionState.CONNECTED_READ_ONLY, ConnectionState.DEGRADED),
        (ConnectionState.CONNECTED_READ_ONLY, ConnectionState.STALE),
        (ConnectionState.CONNECTED_READ_ONLY, ConnectionState.RECONCILIATION_REQUIRED),
        (ConnectionState.CONNECTED_READ_ONLY, ConnectionState.DISCONNECTED),
        (ConnectionState.CONNECTED_READ_ONLY, ConnectionState.BLOCKED),
        (ConnectionState.DEGRADED, ConnectionState.CONNECTED_READ_ONLY),
        (ConnectionState.DEGRADED, ConnectionState.STALE),
        (ConnectionState.DEGRADED, ConnectionState.BLOCKED),
        (ConnectionState.DEGRADED, ConnectionState.DISCONNECTED),
        (ConnectionState.STALE, ConnectionState.RECONCILIATION_REQUIRED),
        (ConnectionState.STALE, ConnectionState.CONNECTED_READ_ONLY),
        (ConnectionState.STALE, ConnectionState.DISCONNECTED),
        (ConnectionState.STALE, ConnectionState.BLOCKED),
        (ConnectionState.RECONCILIATION_REQUIRED, ConnectionState.CONNECTED_READ_ONLY),
        (ConnectionState.RECONCILIATION_REQUIRED, ConnectionState.BLOCKED),
        (ConnectionState.RECONCILIATION_REQUIRED, ConnectionState.DISCONNECTED),
        (ConnectionState.BLOCKED, ConnectionState.DISCONNECTED),
    }
)

_LOCK = Lock()
_STATE = ConnectionState.DISCONNECTED


def current() -> ConnectionState:
    return _STATE


def reset_for_tests() -> None:
    global _STATE
    with _LOCK:
        _STATE = ConnectionState.DISCONNECTED


def force(value: ConnectionState) -> ConnectionState:
    global _STATE
    with _LOCK:
        _STATE = value
        return _STATE


def transition(target: ConnectionState) -> ConnectionState:
    global _STATE
    with _LOCK:
        if (_STATE, target) not in LEGAL:
            raise InvalidBrokerTransition(f"{_STATE.value} → {target.value} is illegal")
        _STATE = target
        return _STATE


def is_healthy(state: ConnectionState | None = None) -> bool:
    value = state if state is not None else current()
    return value is ConnectionState.CONNECTED_READ_ONLY
