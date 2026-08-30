"""Explicit recovery. Silent recovery is FAIL."""

from __future__ import annotations

from quantlab.ops.errors import InvalidOpsTransition
from quantlab.ops.state import FATAL, OpsState, current, transition


def recover(*, explicit: bool) -> OpsState:
    if not explicit:
        raise InvalidOpsTransition("silent recovery is forbidden")
    if current() not in FATAL | {OpsState.HALTED, OpsState.RECOVERY, OpsState.DEGRADED}:
        raise InvalidOpsTransition(f"{current().value} is not a recovery source")
    if current() is not OpsState.RECOVERY:
        transition(OpsState.RECOVERY)
    return transition(OpsState.READY)
