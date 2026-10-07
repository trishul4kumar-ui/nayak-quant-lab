"""Durable, append-only position-review persistence."""

from __future__ import annotations

from pathlib import Path

from quantlab.agents.repository import AgentRepository
from quantlab.position_intelligence.models import PositionAssessment, PositionReviewSchedule


class PositionIntelligenceRepository:
    def __init__(self, path: Path | None = None) -> None:
        self._artifacts = AgentRepository(path)

    def put_assessment(self, assessment: PositionAssessment) -> PositionAssessment:
        return self._artifacts.put(assessment)

    def put_schedule(self, schedule: PositionReviewSchedule) -> PositionReviewSchedule:
        return self._artifacts.put(schedule)

    def assessments(self) -> tuple[PositionAssessment, ...]:
        return self._artifacts.list(PositionAssessment)

    def schedules(self) -> tuple[PositionReviewSchedule, ...]:
        return self._artifacts.list(PositionReviewSchedule)

    def close(self) -> None:
        self._artifacts.close()
