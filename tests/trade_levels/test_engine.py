from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from quantlab.agents.hashing import digest
from quantlab.agents.repository import AgentRepository
from quantlab.trade_levels.engine import (
    chart_overlay,
    compute_trade_level_plan,
    default_trade_level_policy,
    evaluate_plan_freshness,
)
from quantlab.trade_levels.models import (
    FreshnessStatus,
    LevelArchetype,
    LevelPlanStatus,
    PriceBasis,
    TradeDirection,
    TradeLevelInput,
    TradeLevelPlan,
)

NOW = datetime(2026, 10, 7, 7, tzinfo=UTC)


def level_input(
    *,
    direction: TradeDirection = TradeDirection.LONG,
    archetype: LevelArchetype = LevelArchetype.BREAKOUT,
    atr: float | None = 2.0,
) -> TradeLevelInput:
    return TradeLevelInput(
        created_at=NOW,
        schema_version="trade-levels-v1",
        adjudication_hash=digest("adjudication"),
        adjudication_outcome=(
            "BULL_DOMINANT" if direction is TradeDirection.LONG else "BEAR_DOMINANT"
        ),
        snapshot_hash=digest("snapshot"),
        security_id="NSE:EXAMPLE",
        direction=direction,
        archetype=archetype,
        as_of=NOW - timedelta(seconds=1),
        expires_at=NOW + timedelta(seconds=60),
        reference_price=100.0,
        atr=atr,
        support_price=97.0,
        resistance_price=101.0,
        bid_price=99.9,
        ask_price=100.1,
        spread_bps=20.0,
        regime="TREND",
        price_basis=PriceBasis.RAW,
        quote_price_basis=PriceBasis.RAW,
        adjustment_policy_id="security-master-v1",
        tick_size=0.05,
        market_session="REGULAR",
        data_quality="valid",
        data_freshness="fresh",
    )


def test_plan_is_deterministic_has_no_quantity_or_execution_authority() -> None:
    value, policy = level_input(), default_trade_level_policy()
    first, first_exit = compute_trade_level_plan(value, policy)
    second, second_exit = compute_trade_level_plan(value, policy)
    assert first == second and first_exit == second_exit
    assert first.status is LevelPlanStatus.READY
    assert first.hard_invalidation < first.protective_stop < first.entry_zone_low
    assert all(target > first.entry_zone_high for target in first.targets)
    assert not first.execution_authority
    with pytest.raises(ValidationError):
        TradeLevelPlan.model_validate({**first.model_dump(mode="python"), "quantity": 4})
    with pytest.raises(ValidationError):
        TradeLevelPlan.model_validate({**first.model_dump(mode="python"), "order_type": "MARKET"})


def test_missing_volatility_invalid_price_and_mixed_basis_fail_closed() -> None:
    with pytest.raises(ValidationError, match="volatility"):
        level_input(atr=None)
    with pytest.raises(ValidationError, match="greater than"):
        TradeLevelInput.model_validate(
            {
                **level_input().model_dump(mode="python", exclude={"content_hash"}),
                "reference_price": 0,
            }
        )
    with pytest.raises(ValidationError, match="basis"):
        TradeLevelInput.model_validate(
            {
                **level_input().model_dump(mode="python", exclude={"content_hash"}),
                "quote_price_basis": PriceBasis.ADJUSTED,
            }
        )


def test_tick_rounding_and_short_side_direction_are_deterministic() -> None:
    plan, _ = compute_trade_level_plan(level_input(direction=TradeDirection.SHORT))
    assert plan.hard_invalidation > plan.protective_stop > plan.entry_zone_high
    assert all(target < plan.entry_zone_low for target in plan.targets)
    assert plan.entry_zone_low / 0.05 == pytest.approx(round(plan.entry_zone_low / 0.05))


def test_no_valid_entry_is_not_a_fabricated_plan() -> None:
    plan, exit_policy = compute_trade_level_plan(
        level_input(archetype=LevelArchetype.NO_VALID_ENTRY, atr=None)
    )
    assert plan.status is LevelPlanStatus.NO_VALID_ENTRY
    assert plan.entry_zone_low is None and plan.targets == () and exit_policy is None


def test_staleness_is_an_immutable_separate_assessment() -> None:
    plan, _ = compute_trade_level_plan(level_input())
    result = evaluate_plan_freshness(
        plan,
        default_trade_level_policy(),
        now=NOW + timedelta(seconds=2),
        current_price=105.0,
        current_atr=4.0,
        current_regime="RANGE",
    )
    assert result.status is FreshnessStatus.STALE_LEVEL_PLAN
    assert set(result.reasons) == {
        "PRICE_MOVED_OUTSIDE_TOLERANCE",
        "VOLATILITY_MOVED_OUTSIDE_TOLERANCE",
        "REGIME_CHANGED",
    }
    overlay = chart_overlay(plan)
    assert overlay.plan_hash == plan.content_hash
    assert overlay.targets == plan.targets


def test_plan_and_exit_policy_survive_control_plane_restart(tmp_path) -> None:
    plan, exit_policy = compute_trade_level_plan(level_input())
    assert exit_policy is not None
    path = tmp_path / "level_artifacts.sqlite"
    repository = AgentRepository(path)
    try:
        repository.put(plan)
        repository.put(exit_policy)
    finally:
        repository.close()
    repository = AgentRepository(path)
    try:
        assert repository.get(plan.content_hash, TradeLevelPlan) == plan
        assert repository.get(exit_policy.content_hash, type(exit_policy)) == exit_policy
    finally:
        repository.close()
