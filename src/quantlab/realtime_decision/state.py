"""Decision-cycle state. DECISION ≠ ORDER."""

from __future__ import annotations

from enum import StrEnum
from threading import Lock

from quantlab.realtime_decision.errors import InvalidDecisionTransition


class DecisionState(StrEnum):
    OBSERVING = "observing"
    VALIDATING = "validating"
    READY = "ready"
    COMPUTING = "computing"
    DECIDED = "decided"
    ABSTAINED = "abstained"
    BLOCKED = "blocked"
    STALE = "stale"
    HALTED = "halted"
    ERROR = "error"


LEGAL: frozenset[tuple[DecisionState, DecisionState]] = frozenset(
    {
        (DecisionState.OBSERVING, DecisionState.VALIDATING),
        (DecisionState.VALIDATING, DecisionState.READY),
        (DecisionState.VALIDATING, DecisionState.ABSTAINED),
        (DecisionState.VALIDATING, DecisionState.BLOCKED),
        (DecisionState.VALIDATING, DecisionState.STALE),
        (DecisionState.VALIDATING, DecisionState.ERROR),
        (DecisionState.READY, DecisionState.COMPUTING),
        (DecisionState.READY, DecisionState.ABSTAINED),
        (DecisionState.READY, DecisionState.BLOCKED),
        (DecisionState.COMPUTING, DecisionState.DECIDED),
        (DecisionState.COMPUTING, DecisionState.ABSTAINED),
        (DecisionState.COMPUTING, DecisionState.BLOCKED),
        (DecisionState.COMPUTING, DecisionState.ERROR),
        (DecisionState.DECIDED, DecisionState.OBSERVING),
        (DecisionState.ABSTAINED, DecisionState.OBSERVING),
        (DecisionState.BLOCKED, DecisionState.OBSERVING),
        (DecisionState.STALE, DecisionState.OBSERVING),
        (DecisionState.ERROR, DecisionState.OBSERVING),
        (DecisionState.HALTED, DecisionState.OBSERVING),
        (DecisionState.READY, DecisionState.HALTED),
        (DecisionState.COMPUTING, DecisionState.HALTED),
        (DecisionState.OBSERVING, DecisionState.HALTED),
        (DecisionState.VALIDATING, DecisionState.HALTED),
    }
)

_LOCK = Lock()
_STATE = DecisionState.OBSERVING


def current() -> DecisionState:
    return _STATE


def reset_for_tests() -> None:
    global _STATE
    with _LOCK:
        _STATE = DecisionState.OBSERVING


def force(value: DecisionState) -> DecisionState:
    global _STATE
    with _LOCK:
        _STATE = value
        return _STATE


def transition(target: DecisionState) -> DecisionState:
    global _STATE
    with _LOCK:
        if (_STATE, target) not in LEGAL:
            raise InvalidDecisionTransition(f"{_STATE.value} → {target.value} is illegal")
        _STATE = target
        return _STATE
