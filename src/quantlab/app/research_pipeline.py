"""Research pipeline stages — idea → backtest → validate → journal → live."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.jobs import JobStatus
from quantlab.app.mode import AppMode
from quantlab.app.queries import last_validation_row


class PipelineStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PASS = "pass"
    FAIL = "fail"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class PipelineStage:
    key: str
    label: str
    nav_key: str
    status: PipelineStatus
    detail: str = ""


def _job_active(runtime: ApplicationRuntime, job_type: str) -> bool:
    for job in runtime.jobs.list_jobs():
        if job.type != job_type:
            continue
        if job.status in {JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.CANCELLING}:
            return True
    return False


def build_research_pipeline(runtime: ApplicationRuntime) -> list[PipelineStage]:
    prefs = runtime.ui_settings.current
    milestones = set(prefs.milestones)
    runs = runtime.ledger.list_runs()
    notes = prefs.journal_notes
    has_note = any(value.strip() for value in notes.values())

    if "onboarding_complete" in milestones:
        idea = PipelineStage("idea", "Idea", "learn", PipelineStatus.PASS, "Hypothesis framed")
    else:
        idea = PipelineStage("idea", "Idea", "learn", PipelineStatus.PENDING, "Complete onboarding")

    if _job_active(runtime, "backtest"):
        backtest = PipelineStage(
            "backtest", "Backtest", "test", PipelineStatus.RUNNING, "Job running"
        )
    elif runs:
        backtest = PipelineStage(
            "backtest", "Backtest", "test", PipelineStatus.PASS, f"{len(runs)} run(s)"
        )
    else:
        backtest = PipelineStage(
            "backtest", "Backtest", "test", PipelineStatus.PENDING, "Run Test wizard"
        )

    val_row = last_validation_row(runtime)
    if _job_active(runtime, "validate"):
        validate = PipelineStage(
            "validate", "Validate", "validation", PipelineStatus.RUNNING, "Suite running"
        )
    elif val_row is None:
        validate = PipelineStage(
            "validate", "Validate", "validation", PipelineStatus.PENDING, "Not run yet"
        )
    else:
        gate = str(val_row.get("gate_outcome") or "").lower()
        if gate == "pass":
            validate = PipelineStage(
                "validate", "Validate", "validation", PipelineStatus.PASS, "Gate passed"
            )
        elif gate in {"fail", "failed"}:
            validate = PipelineStage(
                "validate", "Validate", "validation", PipelineStatus.FAIL, "Gate failed"
            )
        else:
            validate = PipelineStage(
                "validate",
                "Validate",
                "validation",
                PipelineStatus.PASS,
                "Complete — review gate",
            )

    if has_note:
        journal = PipelineStage("journal", "Journal", "journal", PipelineStatus.PASS, "Notes saved")
    elif runs:
        journal = PipelineStage(
            "journal", "Journal", "journal", PipelineStatus.PENDING, "Add a note"
        )
    else:
        journal = PipelineStage(
            "journal", "Journal", "journal", PipelineStatus.PENDING, "After first run"
        )

    if runtime.mode is AppMode.LIVE:
        live = PipelineStage("live", "Live", "broker", PipelineStatus.PASS, "LIVE mode active")
    elif not runtime.gates.all_pass():
        live = PipelineStage(
            "live", "Live", "broker", PipelineStatus.BLOCKED, "Safety gates incomplete"
        )
    elif prefs.broker_wizard_complete:
        live = PipelineStage(
            "live", "Live", "broker", PipelineStatus.PENDING, "Paper ready — gates pending"
        )
    else:
        live = PipelineStage(
            "live", "Live", "broker", PipelineStatus.BLOCKED, "Complete broker wizard"
        )

    return [idea, backtest, validate, journal, live]
