"""Pure, deterministic level arithmetic with explicit failure boundaries."""

from __future__ import annotations

from datetime import UTC, datetime
from math import ceil, floor

from quantlab.agents.hashing import digest
from quantlab.trade_levels.models import (
    ExitPolicy,
    ExitRule,
    ExitRuleName,
    FreshnessStatus,
    LevelArchetype,
    LevelPlanStatus,
    PlanFreshness,
    TradeChartOverlayDTO,
    TradeDirection,
    TradeLevelInput,
    TradeLevelPlan,
    TradeLevelPolicy,
)

POLICY_TIME = datetime(2026, 10, 7, tzinfo=UTC)


def default_trade_level_policy() -> TradeLevelPolicy:
    return TradeLevelPolicy(
        created_at=POLICY_TIME,
        schema_version="trade-levels-v1",
        policy_id="44-v1",
        entry_band_atr=0.10,
        protective_stop_atr=1.0,
        hard_invalidation_atr=1.25,
        target_atr_multiples=(2.0, 3.0),
        trailing_atr=1.5,
        max_price_move_bps=75,
        max_volatility_change_ratio=1.5,
        max_snapshot_age_seconds=300,
    )


def _round_down(value: float, tick_size: float) -> float:
    return round(floor(value / tick_size) * tick_size, 10)


def _round_up(value: float, tick_size: float) -> float:
    return round(ceil(value / tick_size) * tick_size, 10)


def _exit_policy(value: TradeLevelInput, policy: TradeLevelPolicy) -> ExitPolicy:
    rules = (
        (ExitRuleName.HARD_INVALIDATION, "Price crosses deterministic hard invalidation."),
        (ExitRuleName.PROTECTIVE_STOP, "Price crosses deterministic protective stop."),
        (ExitRuleName.PROFIT_TARGET, "Price reaches a deterministic target level."),
        (ExitRuleName.TRAILING_STOP, f"Trail by {policy.trailing_atr:g} approved ATR."),
        (ExitRuleName.TIME_STOP, "Maximum holding window expires."),
        (ExitRuleName.REGIME_EXIT, "Frozen regime no longer matches current regime."),
        (ExitRuleName.LIQUIDITY_EXIT, "Required liquidity/spread state is no longer available."),
        (ExitRuleName.VOLATILITY_SHOCK_EXIT, "Volatility changes outside policy tolerance."),
        (ExitRuleName.SESSION_EXIT, "Market session is no longer the required session."),
    )
    return ExitPolicy(
        created_at=value.created_at,
        schema_version="trade-levels-v1",
        policy_id=f"{policy.policy_id}-exit",
        direction=value.direction,
        rules=tuple(
            ExitRule(
                created_at=value.created_at,
                schema_version="trade-levels-v1",
                rule=rule,
                condition=condition,
                version=policy.policy_id,
            )
            for rule, condition in rules
        ),
    )


def _entry_anchor(value: TradeLevelInput) -> float:
    """Choose only from frozen numerical inputs, never from agent prose."""
    assert value.atr is not None
    if value.archetype is LevelArchetype.BREAKOUT:
        return (
            max(value.reference_price, value.resistance_price or value.reference_price)
            + 0.1 * value.atr
        )
    if value.archetype is LevelArchetype.BREAKDOWN:
        return (
            min(value.reference_price, value.support_price or value.reference_price)
            - 0.1 * value.atr
        )
    if value.archetype in {LevelArchetype.PULLBACK, LevelArchetype.MEAN_REVERSION_RECOVERY}:
        return min(value.reference_price, value.support_price or value.reference_price)
    if value.archetype in {LevelArchetype.LIMIT_ZONE, LevelArchetype.FAILED_BREAKOUT}:
        return value.resistance_price or value.reference_price
    if value.archetype in {LevelArchetype.MOMENTUM_CONTINUATION, LevelArchetype.VOLATILITY_TRIGGER}:
        return value.reference_price
    raise ValueError("unsupported entry archetype")


def _validate_eligible(value: TradeLevelInput, policy: TradeLevelPolicy) -> None:
    if value.created_at >= value.expires_at:
        raise ValueError("stale level input")
    if (value.created_at - value.as_of).total_seconds() > policy.max_snapshot_age_seconds:
        raise ValueError("level input exceeds policy freshness")
    if value.adjudication_no_trade:
        raise ValueError("no-trade adjudication cannot generate levels")
    expected = "BULL_DOMINANT" if value.direction is TradeDirection.LONG else "BEAR_DOMINANT"
    if value.adjudication_outcome != expected:
        raise ValueError("adjudication direction does not support requested level plan")


def compute_trade_level_plan(
    value: TradeLevelInput, policy: TradeLevelPolicy | None = None
) -> tuple[TradeLevelPlan, ExitPolicy | None]:
    """Return the same plan/policy for identical sealed input artifacts."""
    value = value.verified()
    policy = (policy or default_trade_level_policy()).verified()
    _validate_eligible(value, policy)
    common = dict(
        created_at=value.created_at,
        schema_version="trade-levels-v1",
        plan_id=digest(
            {
                "input_hash": value.content_hash,
                "policy_hash": policy.content_hash,
                "contract": "TradeLevelPlan",
            }
        )[:32],
        security_id=value.security_id,
        direction=value.direction,
        as_of=value.as_of,
        expires_at=value.expires_at,
        snapshot_hash=value.snapshot_hash,
        adjudication_hash=value.adjudication_hash,
        archetype=value.archetype,
        price_basis=value.price_basis,
        tick_size=value.tick_size,
        adjustment_policy_id=value.adjustment_policy_id,
        required_market_state=(
            "FRESH_CANONICAL_SNAPSHOT",
            f"SESSION:{value.market_session}",
            f"REGIME:{value.regime}",
            "LIQUID_QUOTE_REQUIRED",
        ),
        warnings=("LEVELS_ARE_RESEARCH_DIAGNOSTICS_NOT_EXECUTION_INSTRUCTIONS",),
        not_tested=(),
        level_policy_hash=policy.content_hash,
        reference_atr=value.atr,
        reference_regime=value.regime,
    )
    if value.archetype is LevelArchetype.NO_VALID_ENTRY:
        return (
            TradeLevelPlan.model_validate(
                {
                    **common,
                    "status": LevelPlanStatus.NO_VALID_ENTRY,
                    "entry_zone_low": None,
                    "entry_zone_high": None,
                    "preferred_reference_price": None,
                    "hard_invalidation": None,
                    "protective_stop": None,
                    "targets": (),
                    "trailing_rule": None,
                    "time_stop": None,
                    "max_holding_period": None,
                    "exit_policy_hash": None,
                }
            ),
            None,
        )
    assert value.atr is not None
    exit_policy = _exit_policy(value, policy)
    anchor = _entry_anchor(value)
    band = policy.entry_band_atr * value.atr
    if value.direction is TradeDirection.LONG:
        entry_low = _round_down(anchor - band, value.tick_size)
        entry_high = _round_up(anchor + band, value.tick_size)
        protective_stop = _round_down(
            entry_low - policy.protective_stop_atr * value.atr, value.tick_size
        )
        hard_invalidation = _round_down(
            entry_low - policy.hard_invalidation_atr * value.atr, value.tick_size
        )
        targets = tuple(
            _round_up(entry_high + multiple * value.atr, value.tick_size)
            for multiple in policy.target_atr_multiples
        )
    else:
        entry_low = _round_down(anchor - band, value.tick_size)
        entry_high = _round_up(anchor + band, value.tick_size)
        protective_stop = _round_up(
            entry_high + policy.protective_stop_atr * value.atr, value.tick_size
        )
        hard_invalidation = _round_up(
            entry_high + policy.hard_invalidation_atr * value.atr, value.tick_size
        )
        targets = tuple(
            _round_down(entry_low - multiple * value.atr, value.tick_size)
            for multiple in policy.target_atr_multiples
        )
    return (
        TradeLevelPlan.model_validate(
            {
                **common,
                "status": LevelPlanStatus.READY,
                "entry_zone_low": entry_low,
                "entry_zone_high": entry_high,
                "preferred_reference_price": round(anchor, 10),
                "hard_invalidation": hard_invalidation,
                "protective_stop": protective_stop,
                "targets": targets,
                "trailing_rule": f"{policy.trailing_atr:g} ATR trailing rule",
                "time_stop": "SESSION_OR_MAX_HOLDING_WINDOW",
                "max_holding_period": "ONE_MARKET_SESSION",
                "exit_policy_hash": exit_policy.content_hash,
            }
        ),
        exit_policy,
    )


def evaluate_plan_freshness(
    plan: TradeLevelPlan,
    policy: TradeLevelPolicy,
    *,
    now: datetime,
    current_price: float,
    current_atr: float,
    current_regime: str,
) -> PlanFreshness:
    """Assess, rather than mutate, a frozen plan when market conditions move."""
    plan, policy = plan.verified(), policy.verified()
    if now.tzinfo is None:
        raise ValueError("freshness time must be timezone-aware")
    if current_price <= 0 or current_atr <= 0 or not current_regime:
        raise ValueError("current canonical market state is required")
    reasons: list[str] = []
    if now >= plan.expires_at:
        reasons.append("PLAN_EXPIRED")
    if plan.preferred_reference_price is not None:
        move_bps = (
            abs(current_price - plan.preferred_reference_price)
            / plan.preferred_reference_price
            * 10_000
        )
        if move_bps > policy.max_price_move_bps:
            reasons.append("PRICE_MOVED_OUTSIDE_TOLERANCE")
    if (
        plan.reference_atr is None
        or current_atr / plan.reference_atr > policy.max_volatility_change_ratio
    ):
        reasons.append("VOLATILITY_MOVED_OUTSIDE_TOLERANCE")
    if plan.reference_regime != current_regime:
        reasons.append("REGIME_CHANGED")
    return PlanFreshness(
        created_at=now.astimezone(UTC),
        schema_version="trade-levels-v1",
        plan_hash=plan.content_hash,
        status=FreshnessStatus.STALE_LEVEL_PLAN if reasons else FreshnessStatus.FRESH,
        reasons=tuple(reasons),
        current_price=current_price,
        current_atr=current_atr,
        current_regime=current_regime,
    )


def chart_overlay(plan: TradeLevelPlan) -> TradeChartOverlayDTO:
    """Create a read-only visual projection; renderers receive no authority."""
    return TradeChartOverlayDTO(
        created_at=plan.created_at,
        schema_version="trade-levels-v1",
        plan_hash=plan.content_hash,
        entry_zone_low=plan.entry_zone_low,
        entry_zone_high=plan.entry_zone_high,
        hard_invalidation=plan.hard_invalidation,
        protective_stop=plan.protective_stop,
        targets=plan.targets,
        trailing_rule=plan.trailing_rule,
        time_horizon=plan.max_holding_period,
        evidence_markers=(plan.adjudication_hash, plan.snapshot_hash),
    )
