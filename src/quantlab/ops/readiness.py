"""Readiness and liveness. Unknown is not ready. False positives are FAIL."""

from __future__ import annotations

from quantlab.core.config import LiveSafetyGates
from quantlab.ops.audit import writer_healthy
from quantlab.ops.models import HealthStatus
from quantlab.ops.state import FATAL, OpsState, current
from quantlab.ops.supervisor import processes


def ready() -> bool:
    if current() in FATAL:
        return False
    if current() not in {OpsState.READY, OpsState.RUNNING, OpsState.DEGRADED}:
        return False
    if LiveSafetyGates().live_trading:
        return False
    return writer_healthy()


def live() -> bool:
    """Process liveness, not live trading."""
    return current() not in FATAL


def readiness_report() -> dict[str, object]:
    status = HealthStatus.HEALTHY if ready() else HealthStatus.FAILED
    if current() is OpsState.DEGRADED:
        status = HealthStatus.DEGRADED
    if current() is OpsState.HALTED:
        status = HealthStatus.HALTED
    procs = processes()
    return {
        "ready": ready(),
        "live": live(),
        "status": status.value,
        "live_trading": False,
        "process_count": len(procs),
        "note": "ready is not permission to trade",
    }
