"""Safety-gateway state. Unknown is never treated as safe."""

from __future__ import annotations

from enum import StrEnum
from threading import Lock

from quantlab.safety.errors import InvalidSafetyTransition


class SafetyState(StrEnum):
    DISABLED = "disabled"
    RESEARCH_ONLY = "research_only"
    PAPER = "paper"
    SHADOW = "shadow"
    ARMED = "armed"
    AUTHORIZED = "authorized"
    RELEASE_BLOCKED = "release_blocked"
    HALTED = "halted"
    EMERGENCY = "emergency"
    RECOVERY_PENDING = "recovery_pending"


LEGAL: frozenset[tuple[SafetyState, SafetyState]] = frozenset(
    {
        (SafetyState.DISABLED, SafetyState.RESEARCH_ONLY),
        (SafetyState.RESEARCH_ONLY, SafetyState.DISABLED),
        (SafetyState.RESEARCH_ONLY, SafetyState.PAPER),
        (SafetyState.PAPER, SafetyState.RESEARCH_ONLY),
        (SafetyState.PAPER, SafetyState.SHADOW),
        (SafetyState.SHADOW, SafetyState.PAPER),
        (SafetyState.SHADOW, SafetyState.ARMED),
        (SafetyState.SHADOW, SafetyState.HALTED),
        (SafetyState.SHADOW, SafetyState.RELEASE_BLOCKED),
        (SafetyState.ARMED, SafetyState.SHADOW),
        (SafetyState.ARMED, SafetyState.AUTHORIZED),
        (SafetyState.ARMED, SafetyState.HALTED),
        (SafetyState.ARMED, SafetyState.RELEASE_BLOCKED),
        (SafetyState.AUTHORIZED, SafetyState.RELEASE_BLOCKED),
        (SafetyState.AUTHORIZED, SafetyState.HALTED),
        (SafetyState.AUTHORIZED, SafetyState.SHADOW),
        (SafetyState.RELEASE_BLOCKED, SafetyState.SHADOW),
        (SafetyState.RELEASE_BLOCKED, SafetyState.HALTED),
        (SafetyState.RELEASE_BLOCKED, SafetyState.ARMED),
        (SafetyState.HALTED, SafetyState.RECOVERY_PENDING),
        (SafetyState.EMERGENCY, SafetyState.RECOVERY_PENDING),
        (SafetyState.RECOVERY_PENDING, SafetyState.RESEARCH_ONLY),
        (SafetyState.RECOVERY_PENDING, SafetyState.PAPER),
        (SafetyState.RECOVERY_PENDING, SafetyState.SHADOW),
    }
)

_LOCK = Lock()
_STATE = SafetyState.RESEARCH_ONLY


def current() -> SafetyState:
    return _STATE


def reset_for_tests() -> None:
    global _STATE
    with _LOCK:
        _STATE = SafetyState.RESEARCH_ONLY


def force(value: SafetyState) -> SafetyState:
    global _STATE
    with _LOCK:
        _STATE = value
        return _STATE


def transition(target: SafetyState) -> SafetyState:
    global _STATE
    with _LOCK:
        if target is SafetyState.EMERGENCY:
            _STATE = SafetyState.EMERGENCY
            return _STATE
        pair = (_STATE, target)
        if pair not in LEGAL:
            raise InvalidSafetyTransition(f"{_STATE.value} → {target.value} is illegal")
        _STATE = target
        return _STATE
