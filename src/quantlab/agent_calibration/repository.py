"""Append-only calibration dataset and scorecard persistence."""

from __future__ import annotations

from pathlib import Path

from quantlab.agent_calibration.models import AgentScorecard, RealizedOutcome
from quantlab.agents.repository import AgentRepository


class CalibrationRepository:
    def __init__(self, path: Path | None = None) -> None:
        self._artifacts = AgentRepository(path)

    def put_outcome(self, outcome: RealizedOutcome) -> RealizedOutcome:
        return self._artifacts.put(outcome)

    def put_scorecard(self, scorecard: AgentScorecard) -> AgentScorecard:
        return self._artifacts.put(scorecard)

    def outcomes(self) -> tuple[RealizedOutcome, ...]:
        return self._artifacts.list(RealizedOutcome)

    def scorecards(self) -> tuple[AgentScorecard, ...]:
        return self._artifacts.list(AgentScorecard)

    def close(self) -> None:
        self._artifacts.close()
