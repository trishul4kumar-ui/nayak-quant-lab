from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from quantlab.agents.hashing import digest
from quantlab.position_intelligence.engine import assess_position
from quantlab.position_intelligence.models import (
    ExitRuleState,
    PositionMode,
    PositionReviewContext,
    PositionReviewSchedule,
    PositionView,
    ReviewTrigger,
    SuggestedStance,
)
from quantlab.position_intelligence.repository import PositionIntelligenceRepository

NOW = datetime(2026, 10, 7, 7, tzinfo=UTC)


def context(*, triggered: bool = False, freshness: str = "fresh") -> PositionReviewContext:
    return PositionReviewContext(
        created_at=NOW,
        schema_version="position-intelligence-v1",
        position_id="paper-position-1",
        mode=PositionMode.PAPER,
        original_candidate_hash=digest("candidate"),
        original_level_plan_hash=digest("plan"),
        original_exit_policy_hash=digest("exit"),
        original_thesis="Trend continuation conditional on fresh liquidity.",
        entry_fill_hash=digest("fill"),
        snapshot_hash=digest("snapshot"),
        current_price=101,
        entry_price=100,
        unrealized_pnl=1,
        pnl_attribution=("price_return=1.0",),
        factor_summary_hash=digest("factors"),
        regime="TREND",
        volatility=2,
        liquidity_status="PASS",
        portfolio_risk_hash=digest("risk"),
        position_opened_at=NOW - timedelta(minutes=5),
        trigger=ReviewTrigger.SCHEDULED,
        exit_rules=(
            ExitRuleState(
                created_at=NOW,
                schema_version="position-intelligence-v1",
                rule="PROTECTIVE_STOP",
                triggered=triggered,
                evidence_refs=(digest("stop"),),
            ),
        ),
        market_freshness=freshness,
    )


def view(role: str, value: PositionReviewContext, status: str = "INTACT") -> PositionView:
    return PositionView(
        created_at=NOW,
        schema_version="position-intelligence-v1",
        role=role,
        context_hash=value.content_hash,
        thesis_status=status,
        evidence_refs=(digest(role),),
        confidence=0.6,
        commentary="Bounded research commentary; no position control.",
    )


def test_triggered_exit_cannot_be_overridden_by_bull() -> None:
    value = context(triggered=True)
    assessment = assess_position(value, view("BULL", value), view("BEAR", value))
    assert assessment.suggested_stance is SuggestedStance.EXIT_CANDIDATE
    assert assessment.thesis_status == "INVALIDATED"


def test_stale_market_blocks_ordinary_assessment() -> None:
    value = context(freshness="stale")
    assessment = assess_position(value, view("BULL", value), view("BEAR", value))
    assert assessment.suggested_stance is SuggestedStance.MORE_RESEARCH
    assert "MARKET_STATE_NOT_FRESH" in assessment.hard_blockers


def test_same_context_is_required_for_opposing_views() -> None:
    value = context()
    other = context(triggered=True)
    with pytest.raises(ValueError, match="same frozen"):
        assess_position(value, view("BULL", value), view("BEAR", other))


def test_closed_position_stops_review_and_schedule_survives_restart(tmp_path: Path) -> None:
    value = context().model_copy(update={"position_closed": True})
    value = PositionReviewContext.model_validate(
        value.model_dump(mode="json", exclude={"content_hash"})
    )
    assessment = assess_position(value, view("BULL", value), view("BEAR", value))
    assert assessment.suggested_stance is SuggestedStance.MORE_RESEARCH
    assert "POSITION_ALREADY_CLOSED" in assessment.hard_blockers

    path = tmp_path / "position.sqlite"
    repository = PositionIntelligenceRepository(path)
    try:
        repository.put_schedule(
            PositionReviewSchedule(
                created_at=NOW,
                schema_version="position-intelligence-v1",
                position_id=value.position_id,
                next_review_at=NOW + timedelta(minutes=15),
                last_context_hash=value.content_hash,
                enabled=False,
            )
        )
    finally:
        repository.close()
    restarted = PositionIntelligenceRepository(path)
    try:
        assert restarted.schedules()[-1].enabled is False
    finally:
        restarted.close()
