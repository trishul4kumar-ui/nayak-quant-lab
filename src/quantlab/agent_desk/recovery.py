"""Restart planning that never replays completed work or an order action."""

from __future__ import annotations

from datetime import datetime

from quantlab.agent_desk.models import DailyDeskState, DeskJob, DeskJobStatus, RecoveryReport
from quantlab.trade_candidates.models import TradeCandidatePacket


def recover_desk(
    state: DailyDeskState,
    jobs: tuple[DeskJob, ...],
    candidates: tuple[TradeCandidatePacket, ...],
    *,
    now: datetime,
) -> RecoveryReport:
    state = state.verified()
    completed = set(state.completed_job_ids)
    resume = tuple(
        job.job_id
        for job in jobs
        if job.status is DeskJobStatus.QUEUED
        and job.job_id not in completed
        and job.safe_research_read
        and job.scheduled_for <= now
        and (job.deadline is None or job.deadline >= now)
    )
    skipped = tuple(
        job.job_id
        for job in jobs
        if job.job_id in completed
        or not job.safe_research_read
        or job.status is DeskJobStatus.COMPLETED
    )
    stale = tuple(candidate.content_hash for candidate in candidates if candidate.expires_at <= now)
    return RecoveryReport(
        created_at=now,
        schema_version="daily-desk-v1",
        desk_state_hash=state.content_hash,
        resumed_job_ids=tuple(sorted(set(resume))),
        skipped_job_ids=tuple(sorted(set(skipped))),
        stale_candidate_hashes=tuple(sorted(set(stale))),
    )
