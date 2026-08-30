"""Twin lifecycle. SHADOW ≠ PAPER ≠ LIVE. DIGITAL TWIN ≠ BROKER."""

from __future__ import annotations

from enum import StrEnum
from threading import Lock

from quantlab.digital_twin.errors import InvalidTwinTransition


class TwinState(StrEnum):
    IDLE = "idle"
    OBSERVING = "observing"
    FROZEN = "frozen"
    DECIDING = "deciding"
    PLANNING = "planning"
    SIMULATING = "simulating"
    ACCOUNTING = "accounting"
    RECONCILING = "reconciling"
    MONITORING = "monitoring"
    REPLAYING = "replaying"
    COMPARING = "comparing"
    HALTED = "halted"
    ERROR = "error"


LEGAL: frozenset[tuple[TwinState, TwinState]] = frozenset(
    {
        (TwinState.IDLE, TwinState.OBSERVING),
        (TwinState.OBSERVING, TwinState.FROZEN),
        (TwinState.FROZEN, TwinState.DECIDING),
        (TwinState.DECIDING, TwinState.PLANNING),
        (TwinState.DECIDING, TwinState.HALTED),
        (TwinState.PLANNING, TwinState.SIMULATING),
        (TwinState.SIMULATING, TwinState.ACCOUNTING),
        (TwinState.ACCOUNTING, TwinState.RECONCILING),
        (TwinState.RECONCILING, TwinState.MONITORING),
        (TwinState.MONITORING, TwinState.IDLE),
        (TwinState.IDLE, TwinState.REPLAYING),
        (TwinState.REPLAYING, TwinState.COMPARING),
        (TwinState.COMPARING, TwinState.IDLE),
        (TwinState.OBSERVING, TwinState.HALTED),
        (TwinState.FROZEN, TwinState.HALTED),
        (TwinState.PLANNING, TwinState.HALTED),
        (TwinState.SIMULATING, TwinState.HALTED),
        (TwinState.HALTED, TwinState.IDLE),
        (TwinState.ERROR, TwinState.IDLE),
        (TwinState.OBSERVING, TwinState.ERROR),
        (TwinState.SIMULATING, TwinState.ERROR),
        (TwinState.IDLE, TwinState.HALTED),
    }
)

_LOCK = Lock()
_STATE = TwinState.IDLE


def current() -> TwinState:
    return _STATE


def reset_for_tests() -> None:
    global _STATE
    with _LOCK:
        _STATE = TwinState.IDLE


def force(value: TwinState) -> TwinState:
    global _STATE
    with _LOCK:
        _STATE = value
        return _STATE


def transition(target: TwinState) -> TwinState:
    global _STATE
    with _LOCK:
        if (_STATE, target) not in LEGAL:
            raise InvalidTwinTransition(f"{_STATE.value} → {target.value} is illegal")
        _STATE = target
        return _STATE
