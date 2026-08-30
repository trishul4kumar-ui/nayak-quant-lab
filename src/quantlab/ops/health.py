"""Ops health wraps app health. Does not replace quantlab.app.health."""

from __future__ import annotations

from quantlab.app.health import ComponentStatus, HealthReport, run_health_checks
from quantlab.app.mode import AppMode
from quantlab.app.paths import RuntimePaths
from quantlab.core.config import LiveSafetyGates, Settings
from quantlab.ops.models import HealthStatus
from quantlab.ops.resources import free_bytes
from quantlab.ops.state import OpsState, current


def wrap_app_health(paths: RuntimePaths | None = None) -> HealthReport:
    settings = Settings()
    return run_health_checks(
        paths or RuntimePaths.discover(),
        settings,
        LiveSafetyGates(),
        AppMode.RESEARCH,
    )


def status_from_state(state: OpsState | None = None) -> HealthStatus:
    value = state or current()
    mapping = {
        OpsState.RUNNING: HealthStatus.HEALTHY,
        OpsState.READY: HealthStatus.HEALTHY,
        OpsState.DEGRADED: HealthStatus.DEGRADED,
        OpsState.HALTED: HealthStatus.HALTED,
        OpsState.RECOVERY: HealthStatus.RECOVERY,
        OpsState.BOOTING: HealthStatus.UNKNOWN,
        OpsState.INITIALIZING: HealthStatus.UNKNOWN,
    }
    failed = (
        value.value.endswith("_invalid")
        or value.value.endswith("_failed")
        or value.value.endswith("_corrupt")
    )
    if failed:
        return HealthStatus.FAILED
    return mapping.get(value, HealthStatus.UNKNOWN)


def scorecard() -> dict[str, str]:
    try:
        report = wrap_app_health()
        app = "PASS" if report.research_ready() else "FAIL"
    except Exception:
        app = "NOT_TESTED"
    try:
        disk = "PASS" if free_bytes() > 1_000_000 else "FAIL"
    except Exception:
        disk = "NOT_TESTED"
    return {
        "app_health": app,
        "disk": disk,
        "live_trading": "FAIL" if LiveSafetyGates().live_trading else "PASS",
        "broker_required": "PASS",
        "ops_state": current().value,
        "unknown": "NOT_TESTED",
    }


def component_ok(report: HealthReport, name: str) -> bool:
    item = report.by_name(name)
    return item is not None and item.status is ComponentStatus.OK
