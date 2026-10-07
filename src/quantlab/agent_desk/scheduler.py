"""A caller-driven scheduler tick; no autonomous thread is created."""

from __future__ import annotations

from datetime import datetime

from quantlab.agent_desk.jobs import due_jobs
from quantlab.agent_desk.models import DailyDeskPolicy, DailyDeskState, DeskJob


def schedule_tick(
    state: DailyDeskState,
    jobs: tuple[DeskJob, ...],
    *,
    now: datetime,
    policy: DailyDeskPolicy,
    started_this_interval: int = 0,
    running_model_calls: int = 0,
) -> tuple[DeskJob, ...]:
    """Return bounded due research reads. Dispatch stays outside Phase 49."""
    return due_jobs(
        jobs,
        now=now,
        policy=policy,
        started_this_interval=started_this_interval,
        running_model_calls=running_model_calls,
        paused=state.paused,
    )
