from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from tests.trade_candidates.test_candidate_packet import build_input

from quantlab.agent_desk.daily_cycle import phase_for_session
from quantlab.agent_desk.jobs import due_jobs
from quantlab.agent_desk.market_session import classify_session
from quantlab.agent_desk.models import (
    DailyDeskState,
    DeskJob,
    DeskJobType,
    DeskPhase,
    DeskSession,
)
from quantlab.agent_desk.notifications import candidate_notification
from quantlab.agent_desk.policies import default_daily_desk_policy
from quantlab.agent_desk.recovery import recover_desk
from quantlab.agent_desk.repository import DailyDeskRepository
from quantlab.agent_desk.service import DailyDeskService
from quantlab.data.fabric.calendar import SourcedCalendar, WeekdayCalendar
from quantlab.trade_candidates.builder import build_candidate

NOW = datetime(2026, 10, 8, 4, 30, tzinfo=UTC)


def calendar() -> SourcedCalendar:
    return SourcedCalendar(
        exchange="NSE",
        holidays=frozenset({date(2026, 10, 9)}),
        source="official-nse-calendar-fixture",
        version="fixture-v1",
    )


def job(index: int, job_type: DeskJobType = DeskJobType.BULL_SCAN) -> DeskJob:
    return DeskJob(
        created_at=NOW,
        schema_version="daily-desk-v1",
        job_id=f"job-{index}",
        job_type=job_type,
        priority=100 - index,
        scheduled_for=NOW - timedelta(minutes=1),
        security_scope=("NSE:EXAMPLE",),
        max_attempts=2,
    )


def state(*, completed: tuple[str, ...] = ()) -> DailyDeskState:
    policy = default_daily_desk_policy()
    return DailyDeskState(
        created_at=NOW,
        schema_version="daily-desk-v1",
        desk_id="desk-1",
        session_date="2026-10-08",
        calendar_version="fixture-v1",
        calendar_provenance="official-nse-calendar-fixture",
        session=DeskSession.CONTINUOUS,
        phase=DeskPhase.INTRADAY_RESEARCH,
        policy_hash=policy.content_hash,
        completed_job_ids=completed,
    )


def test_requires_sourced_calendar_and_honors_holiday() -> None:
    with pytest.raises(ValueError, match="SOURCED"):
        classify_session(NOW, WeekdayCalendar())
    holiday = datetime(2026, 10, 9, 5, 0, tzinfo=UTC)
    assert classify_session(holiday, calendar()) is DeskSession.CLOSED
    assert phase_for_session(DeskSession.OPENING) is DeskPhase.OPENING_OBSERVATION


def test_budget_and_pause_bound_due_work() -> None:
    policy = default_daily_desk_policy()
    selected = due_jobs(
        tuple(job(index) for index in range(8)),
        now=NOW,
        policy=policy,
        started_this_interval=0,
        running_model_calls=0,
        paused=False,
    )
    assert len(selected) == policy.max_concurrent_model_calls
    assert due_jobs(
        (job(1),),
        now=NOW,
        policy=policy,
        started_this_interval=0,
        running_model_calls=0,
        paused=True,
    ) == ()


def test_restart_recovery_never_duplicates_completed_jobs_or_expired_candidates() -> None:
    candidate = build_candidate(build_input())
    expired = candidate.model_copy(update={"expires_at": NOW - timedelta(seconds=1)})
    expired = type(candidate).model_validate(
        expired.model_dump(mode="json", exclude={"content_hash"})
    )
    report = recover_desk(state(completed=("job-1",)), (job(1), job(2)), (expired,), now=NOW)
    assert report.resumed_job_ids == ("job-2",)
    assert report.skipped_job_ids == ("job-1",)
    assert report.stale_candidate_hashes == (expired.content_hash,)


def test_action_notification_is_candidate_only_and_deduplicated() -> None:
    candidate = build_candidate(build_input())
    notification = candidate_notification(candidate, now=candidate.created_at, existing=())
    assert notification is not None and not notification.execution_authority
    duplicate = candidate_notification(
        candidate,
        now=candidate.created_at,
        existing=(notification,),
    )
    assert duplicate is None


def test_pause_state_persists_across_restart(tmp_path: Path) -> None:
    path = tmp_path / "daily-desk.sqlite"
    repository = DailyDeskRepository(path)
    try:
        service = DailyDeskService(repository)
        service.start("desk-1", now=NOW, calendar=calendar())
        paused = service.pause("desk-1", now=NOW + timedelta(seconds=1))
        assert paused.phase is DeskPhase.PAUSED
    finally:
        repository.close()
    restarted = DailyDeskRepository(path)
    try:
        assert restarted.latest_state("desk-1") is not None
        assert restarted.latest_state("desk-1").paused  # type: ignore[union-attr]
    finally:
        restarted.close()
