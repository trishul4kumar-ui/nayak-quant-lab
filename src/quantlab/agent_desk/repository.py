"""Append-only persistence for daily desk artifacts."""

from __future__ import annotations

from pathlib import Path

from quantlab.agent_desk.models import (
    DailyDeskPolicy,
    DailyDeskState,
    DeskJob,
    DeskNotification,
    RecoveryReport,
    Watchlist,
)
from quantlab.agents.repository import AgentRepository


class DailyDeskRepository:
    def __init__(self, path: Path | None = None) -> None:
        self._artifacts = AgentRepository(path)

    def put_state(self, state: DailyDeskState) -> DailyDeskState:
        return self._artifacts.put(state)

    def put_policy(self, policy: DailyDeskPolicy) -> DailyDeskPolicy:
        return self._artifacts.put(policy)

    def put_job(self, job: DeskJob) -> DeskJob:
        return self._artifacts.put(job)

    def put_notification(self, notification: DeskNotification) -> DeskNotification:
        return self._artifacts.put(notification)

    def put_recovery(self, report: RecoveryReport) -> RecoveryReport:
        return self._artifacts.put(report)

    def put_watchlist(self, watchlist: Watchlist) -> Watchlist:
        return self._artifacts.put(watchlist)

    def states(self) -> tuple[DailyDeskState, ...]:
        return self._artifacts.list(DailyDeskState)

    def jobs(self) -> tuple[DeskJob, ...]:
        return self._artifacts.list(DeskJob)

    def notifications(self) -> tuple[DeskNotification, ...]:
        return self._artifacts.list(DeskNotification)

    def latest_state(self, desk_id: str) -> DailyDeskState | None:
        rows = [item for item in self.states() if item.desk_id == desk_id]
        return max(rows, key=lambda item: item.created_at) if rows else None

    def close(self) -> None:
        self._artifacts.close()
