"""Bounded, immutable job selection for one scheduler tick."""

from __future__ import annotations

from datetime import datetime

from quantlab.agent_desk.models import DailyDeskPolicy, DeskJob, DeskJobStatus
from quantlab.agent_desk.policies import admits_job


def due_jobs(
    jobs: tuple[DeskJob, ...],
    *,
    now: datetime,
    policy: DailyDeskPolicy,
    started_this_interval: int,
    running_model_calls: int,
    paused: bool,
) -> tuple[DeskJob, ...]:
    """Return a finite ordered work list; callers own any actual research dispatch."""
    if paused:
        return ()
    selected: list[DeskJob] = []
    model_calls = running_model_calls
    for job in sorted(jobs, key=lambda item: (-item.priority, item.scheduled_for, item.job_id)):
        if job.status is not DeskJobStatus.QUEUED or job.scheduled_for > now:
            continue
        if job.deadline is not None and job.deadline < now:
            continue
        if not admits_job(
            job,
            started_this_interval=started_this_interval + len(selected),
            running_model_calls=model_calls,
            policy=policy,
        ):
            continue
        selected.append(job)
        if job.job_type.value in {"BULL_SCAN", "BEAR_SCAN", "DEBATE"}:
            model_calls += 1
        if len(selected) >= policy.maximum_research_jobs_per_tick:
            break
    return tuple(selected)
