from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from quantlab.agent_calibration.models import OutcomeStance, RealizedOutcome, ScoreStatus
from quantlab.agent_calibration.repository import CalibrationRepository
from quantlab.agent_calibration.scoring import score_agent
from quantlab.agents.hashing import digest

NOW = datetime(2026, 10, 7, 7, tzinfo=UTC)


def outcome(index: int, *, confidence: float = 0.8, realized: float = 0.01) -> RealizedOutcome:
    prediction = NOW - timedelta(days=index + 2)
    realized_at = prediction + timedelta(days=1)
    return RealizedOutcome(
        created_at=NOW,
        schema_version="agent-calibration-v1",
        outcome_id=f"outcome-{index}",
        agent_id="bull-v1",
        agent_version="v1",
        memo_hash=digest(f"memo-{index}"),
        candidate_hash=digest(f"candidate-{index}"),
        level_plan_hash=digest(f"plan-{index}"),
        prediction_time=prediction,
        realized_at=realized_at,
        stance=OutcomeStance.LONG,
        raw_confidence=confidence,
        realized_return=realized,
        regime="TREND",
        paper_or_shadow=True,
    )


def test_small_sample_is_not_calibrated() -> None:
    scorecard = score_agent(tuple(outcome(index) for index in range(3)), as_of=NOW)
    assert scorecard.status is ScoreStatus.NOT_TESTED
    assert scorecard.calibrated_confidence is None
    assert "RAW_CONFIDENCE_IS_NOT_CALIBRATED" in scorecard.warnings


def test_released_scorecard_is_reproducible_and_not_self_modifying() -> None:
    records = tuple(outcome(index, realized=0.01 if index % 2 else -0.01) for index in range(20))
    first = score_agent(records, as_of=NOW)
    second = score_agent(records, as_of=NOW)
    assert first == second and first.status is ScoreStatus.RELEASED
    assert first.calibrated_confidence == 0.5
    assert not first.self_modifying


def test_future_outcome_is_rejected_to_prevent_leakage() -> None:
    with pytest.raises(ValueError, match="future"):
        score_agent((outcome(1),), as_of=NOW - timedelta(days=2, seconds=1))


def test_outcomes_and_scorecards_are_immutable_across_restart(tmp_path: Path) -> None:
    records = tuple(outcome(index) for index in range(20))
    scorecard = score_agent(records, as_of=NOW)
    path = tmp_path / "calibration.sqlite"
    repository = CalibrationRepository(path)
    try:
        repository.put_outcome(records[0])
        repository.put_scorecard(scorecard)
    finally:
        repository.close()
    restarted = CalibrationRepository(path)
    try:
        assert restarted.outcomes() == (records[0],)
        assert restarted.scorecards() == (scorecard,)
    finally:
        restarted.close()
