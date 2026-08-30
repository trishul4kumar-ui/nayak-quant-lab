"""Pulse dashboard model — operational status cards for Home."""

from __future__ import annotations

from dataclasses import dataclass

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.health import ComponentStatus
from quantlab.app.jobs import JobStatus
from quantlab.app.status import SystemStatus


@dataclass(frozen=True)
class PulseItem:
    key: str
    title: str
    value: str
    detail: str
    tone: str  # ok | warn | bad | neutral
    nav_key: str = ""


def status_tone(label: str, value: str) -> str:
    v = value.upper()
    if any(word in v for word in ("FAIL", "ERROR", "UNHEALTH", "DEGRADED")):
        return "bad"
    if label in {"BROKER", "LIVE"} and any(w in v for w in ("DISCONNECT", "DISABLE", "BLOCK")):
        return "bad" if label == "LIVE" and "DISABLE" in v else "warn"
    if label == "RISK" and "ARM" in v:
        return "warn"
    if label == "JOBS" and any(w in v for w in ("RUNNING", "QUEUED")):
        return "warn"
    if any(word in v for word in ("READY", "HEALTHY", "OK", "ENABLED", "IDLE")):
        return "ok"
    return "neutral"


def _component_detail(runtime: ApplicationRuntime, name: str, fallback: str = "") -> str:
    component = runtime.health.by_name(name)
    if component is None:
        return fallback
    return component.detail[:64] + ("…" if len(component.detail) > 64 else "")


def _failed_components(runtime: ApplicationRuntime) -> list[str]:
    return [
        c.name
        for c in runtime.health.components
        if c.required and c.status is ComponentStatus.FAILED
    ]


def build_pulse_items(runtime: ApplicationRuntime) -> tuple[str, list[PulseItem], str]:
    """Return summary headline, pulse cards, and summary tone for the Home panel."""
    status: SystemStatus = runtime.refresh_status()
    failed = _failed_components(runtime)
    active_jobs = [
        j
        for j in runtime.jobs.list_jobs()
        if j.status in {JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.CANCELLING}
    ]
    runs = runtime.ledger.list_runs()
    run_count = len(runs)

    if failed:
        summary = f"{len(failed)} component{'s' if len(failed) != 1 else ''} need attention"
        summary_tone = "bad"
    elif status.system.upper() != "HEALTHY":
        summary = "Lab degraded — open System for details"
        summary_tone = "warn"
    elif active_jobs:
        summary = f"{len(active_jobs)} job{'s' if len(active_jobs) != 1 else ''} in progress"
        summary_tone = "warn"
    else:
        summary = "All systems ready for research"
        summary_tone = "ok"

    mode_detail = {
        "research": "Synthetic data · live blocked",
        "paper": "Paper session · no real orders",
        "live": "Live mode — verify gates",
        "development": "Development build",
        "shadow": "Shadow execution",
    }.get(status.mode.value, status.mode.value)

    live_detail = (
        "Safety gates open"
        if "ENABLE" in status.live_trading.upper()
        else "Blocked until gates pass"
    )

    job_value = "IDLE"
    job_detail = f"{run_count} experiment{'s' if run_count != 1 else ''} in ledger"
    if active_jobs:
        types = {j.type for j in active_jobs}
        job_value = f"{len(active_jobs)} ACTIVE"
        job_detail = ", ".join(sorted(types))[:48]

    system_detail = "All required components OK"
    if failed:
        system_detail = ", ".join(failed[:2])
        if len(failed) > 2:
            system_detail += f" +{len(failed) - 2} more"

    items = [
        PulseItem(
            "system",
            "System",
            status.system,
            system_detail,
            status_tone("SYSTEM", status.system),
            "system",
        ),
        PulseItem(
            "data",
            "Data",
            status.data,
            _component_detail(runtime, "data_fabric", "Fabric and store"),
            status_tone("DATA", status.data),
            "data",
        ),
        PulseItem(
            "research",
            "Research",
            status.research,
            _component_detail(runtime, "research_engine", "Backtest pipeline"),
            status_tone("RESEARCH", status.research),
            "backtests",
        ),
        PulseItem(
            "risk",
            "Risk",
            status.risk,
            f"Firewall · state {runtime.risk_state.value}",
            status_tone("RISK", status.risk),
            "risk",
        ),
        PulseItem(
            "broker",
            "Broker",
            status.broker,
            _component_detail(runtime, "broker_gateway", "OpenAlgo / Zerodha"),
            status_tone("BROKER", status.broker),
            "broker",
        ),
        PulseItem(
            "live",
            "Live",
            status.live_trading,
            live_detail,
            status_tone("LIVE", status.live_trading),
            "broker",
        ),
        PulseItem(
            "mode",
            "Mode",
            status.mode.value.upper(),
            mode_detail,
            "warn" if status.mode.value == "live" else "neutral",
            "settings",
        ),
        PulseItem(
            "jobs",
            "Jobs",
            job_value,
            job_detail,
            status_tone("JOBS", job_value),
            "logs" if active_jobs else "experiments",
        ),
    ]
    return summary, items, summary_tone
