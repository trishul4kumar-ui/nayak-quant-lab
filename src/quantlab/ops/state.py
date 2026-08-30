"""Ops lifecycle. Fatal states do not auto-return to RUNNING. Unknown ≠ healthy."""

from __future__ import annotations

from enum import StrEnum
from threading import Lock

from quantlab.ops.errors import InvalidOpsTransition


class OpsState(StrEnum):
    BOOTING = "booting"
    INITIALIZING = "initializing"
    CONFIG_VALIDATION = "config_validation"
    DEPENDENCY_VALIDATION = "dependency_validation"
    DATA_VALIDATION = "data_validation"
    HEALTH_CHECK = "health_check"
    READY = "ready"
    RUNNING = "running"
    DEGRADED = "degraded"
    HALTED = "halted"
    RECOVERY = "recovery"
    CONFIG_INVALID = "config_invalid"
    SECRET_INVALID = "secret_invalid"
    DATA_CORRUPT = "data_corrupt"
    STATE_CORRUPT = "state_corrupt"
    DEPENDENCY_FAILED = "dependency_failed"
    CLOCK_INVALID = "clock_invalid"
    DISK_CRITICAL = "disk_critical"
    AUDIT_FAILURE = "audit_failure"
    RECONCILIATION_FAILURE = "reconciliation_failure"
    SAFETY_FAILURE = "safety_failure"


FATAL: frozenset[OpsState] = frozenset(
    {
        OpsState.CONFIG_INVALID,
        OpsState.SECRET_INVALID,
        OpsState.DATA_CORRUPT,
        OpsState.STATE_CORRUPT,
        OpsState.DEPENDENCY_FAILED,
        OpsState.CLOCK_INVALID,
        OpsState.DISK_CRITICAL,
        OpsState.AUDIT_FAILURE,
        OpsState.RECONCILIATION_FAILURE,
        OpsState.SAFETY_FAILURE,
    }
)

STARTUP: tuple[OpsState, ...] = (
    OpsState.BOOTING,
    OpsState.INITIALIZING,
    OpsState.CONFIG_VALIDATION,
    OpsState.DEPENDENCY_VALIDATION,
    OpsState.DATA_VALIDATION,
    OpsState.HEALTH_CHECK,
    OpsState.READY,
    OpsState.RUNNING,
)

_LOCK = Lock()
_STATE = OpsState.BOOTING


def current() -> OpsState:
    return _STATE


def reset_for_tests() -> None:
    global _STATE
    with _LOCK:
        _STATE = OpsState.BOOTING


def force(value: OpsState) -> OpsState:
    global _STATE
    with _LOCK:
        _STATE = value
        return _STATE


def transition(target: OpsState) -> OpsState:
    global _STATE
    with _LOCK:
        if _STATE in FATAL and target is OpsState.RUNNING:
            raise InvalidOpsTransition(f"{_STATE.value} cannot auto-return to RUNNING")
        allowed_from_fatal = {OpsState.RECOVERY, OpsState.HALTED, OpsState.READY}
        if _STATE in FATAL and target not in allowed_from_fatal and target not in FATAL:
            raise InvalidOpsTransition(
                f"{_STATE.value} → {target.value} requires explicit recovery"
            )
        _STATE = target
        return _STATE


def advance_startup() -> OpsState:
    if current() in FATAL:
        raise InvalidOpsTransition(f"{current().value} is fatal")
    if current() is OpsState.RUNNING:
        return current()
    try:
        idx = STARTUP.index(current())
    except ValueError as exc:
        raise InvalidOpsTransition(f"{current().value} is not a startup state") from exc
    if idx >= len(STARTUP) - 1:
        return current()
    return transition(STARTUP[idx + 1])
