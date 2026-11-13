"""Research pipeline stages — idea → backtest → validate → journal → live."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.jobs import JobStatus
from quantlab.app.mode import AppMode
from quantlab.app.queries import is_validation_run, last_validation_row, selected_research_summary
from quantlab.data.policy import fixtures_enabled


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
    summary = selected_research_summary(runtime)
    selected_ids = set(summary["selected_run_ids"])
    if prefs.selected_backtest_id:
        selected_ids.add(prefs.selected_backtest_id)
    notes = prefs.journal_notes
    has_note = any(value.strip() for key, value in notes.items() if key in selected_ids)

    if "onboarding_complete" in milestones:
        idea = PipelineStage(
            "idea", "Idea", "learn", PipelineStatus.PASS, "Orientation complete; not evidence"
        )
    else:
        idea = PipelineStage("idea", "Idea", "learn", PipelineStatus.PENDING, "Complete onboarding")

    backtest_runs = [
        run
        for run in runs
        if not is_validation_run(run)
        and run.id == prefs.selected_backtest_id
        and (fixtures_enabled() or run.data_kind.lower() == "real")
        and "total_return" in run.metrics
        and run.status.value in {"completed", "passed"}
    ]
    if _job_active(runtime, "backtest") or _job_active(runtime, "market_backtest"):
        backtest = PipelineStage(
            "backtest", "Backtest", "test", PipelineStatus.RUNNING, "Job running"
        )
    elif summary["engines"]:
        backtest = PipelineStage(
            "backtest",
            "Explore",
            "data",
            PipelineStatus.PASS,
            f"{len(summary['engines'])} selected engine(s) computed; validation NOT_TESTED",
        )
    elif backtest_runs:
        backtest = PipelineStage(
            "backtest",
            "Backtest",
            "test",
            PipelineStatus.PASS,
            f"{len(backtest_runs)} computation(s); not validation",
        )
    else:
        backtest = PipelineStage(
            "backtest", "Backtest", "test", PipelineStatus.PENDING, "Run Test wizard"
        )

    parent = str(getattr(prefs, "selected_backtest_id", "")) or None
    candidate = str(getattr(prefs, "selected_candidate_id", "")) or None
    val_row = last_validation_row(runtime, parent_run_id=parent, candidate_id=candidate)
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
        if gate in {"pass", "research_candidate", "promoted_to_paper"} and (parent or candidate):
            validate = PipelineStage(
                "validate",
                "Validate",
                "validation",
                PipelineStatus.PASS,
                f"Research gate: {gate.upper()} · not live",
            )
        elif gate in {"fail", "failed", "reject"}:
            validate = PipelineStage(
                "validate", "Validate", "validation", PipelineStatus.FAIL, "Gate failed"
            )
        else:
            validate = PipelineStage(
                "validate",
                "Validate",
                "validation",
                PipelineStatus.PENDING,
                "Select candidate; historical validation only"
                if not (parent or candidate)
                else "Validation NOT_TESTED — no pass recorded",
            )

    if has_note:
        journal = PipelineStage("journal", "Journal", "journal", PipelineStatus.PASS, "Notes saved")
    elif selected_ids:
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
