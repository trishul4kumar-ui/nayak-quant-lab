"""Thin persistence service for daily desk state; it owns no broker/provider client."""

from __future__ import annotations

from datetime import datetime

from quantlab.agent_desk.daily_cycle import phase_for_session
from quantlab.agent_desk.market_session import classify_session, require_sourced_calendar
from quantlab.agent_desk.models import DailyDeskPolicy, DailyDeskState, DeskPhase
from quantlab.agent_desk.policies import default_daily_desk_policy
from quantlab.agent_desk.repository import DailyDeskRepository
from quantlab.core.time import IST
from quantlab.data.fabric.calendar import TradingCalendar


class DailyDeskService:
    def __init__(
        self, repository: DailyDeskRepository, policy: DailyDeskPolicy | None = None
    ) -> None:
        self.repository = repository
        self.policy = (policy or default_daily_desk_policy()).verified()

    def start(self, desk_id: str, *, now: datetime, calendar: TradingCalendar) -> DailyDeskState:
        calendar = require_sourced_calendar(calendar)
        self.repository.put_policy(self.policy)
        session = classify_session(now, calendar)
        state = DailyDeskState(
            created_at=now,
            schema_version="daily-desk-v1",
            desk_id=desk_id,
            session_date=now.astimezone(IST).date().isoformat(),
            calendar_version=calendar.version,
            calendar_provenance=calendar.provenance,
            session=session,
            phase=phase_for_session(session),
            policy_hash=self.policy.content_hash,
            completed_job_ids=(),
        )
        return self.repository.put_state(state)

    def pause(self, desk_id: str, *, now: datetime) -> DailyDeskState:
        current = self._required_state(desk_id)
        return self.repository.put_state(
            self._replace_state(current, now=now, phase=DeskPhase.PAUSED, paused=True)
        )

    def resume(self, desk_id: str, *, now: datetime, calendar: TradingCalendar) -> DailyDeskState:
        current = self._required_state(desk_id)
        calendar = require_sourced_calendar(calendar)
        session = classify_session(now, calendar)
        return self.repository.put_state(
            self._replace_state(
                current,
                now=now,
                session=session,
                phase=phase_for_session(session),
                paused=False,
                calendar_version=calendar.version,
                calendar_provenance=calendar.provenance,
            )
        )

    def _required_state(self, desk_id: str) -> DailyDeskState:
        current = self.repository.latest_state(desk_id)
        if current is None:
            raise KeyError("daily desk state missing")
        return current

    @staticmethod
    def _replace_state(
        current: DailyDeskState, *, now: datetime, **changes: object
    ) -> DailyDeskState:
        payload = current.model_dump(mode="python", exclude={"content_hash"})
        payload.update(changes)
        payload["created_at"] = now
        return DailyDeskState.model_validate(payload)
