"""Simulated fills. A fill is not a broker confirmation."""

from __future__ import annotations

import math
from datetime import datetime

from quantlab.core.errors import ExecutionResearchError
from quantlab.domain.models import Side
from quantlab.execution_research.costs import explicit_bps
from quantlab.execution_research.definition import (
    ExecutionLeakFlags,
    FillKind,
    FillStatus,
    MarketMicrostructureDefinition,
    OrderIntent,
    SimulatedFill,
)
from quantlab.execution_research.impact import impact_bps
from quantlab.execution_research.participation import max_fillable, participation
from quantlab.execution_research.slippage import slippage_bps
from quantlab.execution_research.spread import spread_bps


def simulate_fill(
    intent: OrderIntent,
    definition: MarketMicrostructureDefinition,
    *,
    arrival_time: datetime,
    arrival_price: float | None,
    volume: float | None,
    trailing_volume: float | None,
    trailing_vol: float | None,
    leaks: ExecutionLeakFlags | None = None,
    future_spread_bps: float | None = None,
) -> SimulatedFill:
    flags = leaks or ExecutionLeakFlags()
    if arrival_time < intent.decision_time and not flags.pre_arrival_fill:
        raise ExecutionResearchError("fill timestamp before decision is invalid")
    if flags.pre_arrival_fill:
        arrival_time = intent.decision_time
        if arrival_price is None:
            arrival_price = intent.reference_price

    spread, _s_status, _s_check, _s_note = spread_bps(
        definition,
        volume=volume,
        trailing_volume=trailing_volume,
        trailing_vol=trailing_vol,
        future_spread_bps=future_spread_bps,
        use_future_spread=flags.future_spread,
    )
    slip, _p_status, _p_check, _p_note = slippage_bps(
        definition,
        spread=spread,
        volume=volume,
        trailing_volume=trailing_volume,
        trailing_vol=trailing_vol,
    )
    requested = float(intent.target_quantity)
    cap = max_fillable(volume, intent.max_participation)
    if flags.full_fill or definition.fill_model is FillKind.FULL:
        filled = requested
    elif volume is None or cap is None:
        filled = 0.0
    else:
        filled = min(requested, cap)
        if definition.fill_model is FillKind.RATIO_CAPPED:
            filled = min(filled, requested * max(0.0, min(definition.fill_ratio_cap, 1.0)))
    remaining = max(requested - filled, 0.0)
    fill_ratio = 0.0 if requested <= 0 else filled / requested
    if remaining <= 1e-12:
        status = FillStatus.FULLY_FILLED
        remaining = 0.0
    elif filled <= 1e-12:
        status = FillStatus.UNFILLED
        filled = 0.0
    else:
        status = FillStatus.PARTIALLY_FILLED
    if flags.hidden_partial_fill:
        status = FillStatus.FULLY_FILLED

    impact, _i_status, _i_check, _i_note = impact_bps(
        definition,
        quantity=filled,
        volume=volume,
        trailing_vol=trailing_vol,
    )
    spread_v = 0.0 if spread is None else float(spread)
    slip_v = 0.0 if slip is None else float(slip)
    impact_v = 0.0 if impact is None else float(impact)
    explicit_v = explicit_bps(definition.cost)
    if flags.wrong_side_slippage:
        slip_v = -abs(slip_v)
    if flags.wrong_side_impact:
        impact_v = -abs(impact_v)

    ref = float(intent.reference_price)
    px = arrival_price if arrival_price is not None and arrival_price > 0 else None
    if filled <= 0 or px is None:
        exec_px = ref
        spread_cost = slippage_cost = impact_cost = explicit_cost = 0.0
        total = 0.0
    else:
        friction = spread_v + abs(slip_v) + abs(impact_v) + explicit_v
        signed_friction = spread_v + slip_v + impact_v + explicit_v
        if intent.side is Side.BUY:
            raw = px * (1.0 + signed_friction / 10_000.0)
        else:
            raw = px * (1.0 - signed_friction / 10_000.0)
        exec_px = _round_tick(raw, definition.tick_size, intent.side)
        notional = filled * px
        spread_cost = notional * spread_v / 10_000.0
        slippage_cost = notional * abs(slip_v) / 10_000.0
        impact_cost = notional * abs(impact_v) / 10_000.0
        explicit_cost = notional * explicit_v / 10_000.0
        if flags.wrong_side_slippage:
            slippage_cost = -slippage_cost
        if flags.wrong_side_impact:
            impact_cost = -impact_cost
        total = spread_cost + slippage_cost + impact_cost + explicit_cost
        if (
            intent.side is Side.BUY
            and exec_px < px
            and friction > 0
            and not flags.wrong_side_slippage
        ):
            raise ExecutionResearchError("BUY execution improved versus arrival price")
        if (
            intent.side is Side.SELL
            and exec_px > px
            and friction > 0
            and not flags.wrong_side_slippage
        ):
            raise ExecutionResearchError("SELL execution improved versus arrival price")

    return SimulatedFill(
        fill_id=f"fill:{intent.intent_id}",
        intent_id=intent.intent_id,
        security_id=intent.security_id,
        timestamp=arrival_time,
        side=intent.side,
        quantity=filled,
        requested_quantity=requested,
        remaining_quantity=remaining,
        fill_ratio=fill_ratio,
        reference_price=ref,
        execution_price=exec_px,
        spread_bps=spread_v,
        slippage_bps=slip_v,
        impact_bps=impact_v,
        explicit_bps=explicit_v,
        spread_cost=spread_cost,
        slippage_cost=slippage_cost,
        impact_cost=impact_cost,
        explicit_cost=explicit_cost,
        total_cost=total,
        fill_status=status,
        participation=participation(filled, volume),
        available_volume=volume,
        model_id=definition.definition_id,
        arrival_time=arrival_time,
        note="simulated fill; not a broker confirmation",
    )


def _round_tick(price: float, tick: float, side: Side) -> float:
    if tick <= 0:
        return price
    steps = price / tick
    if side is Side.BUY:
        return math.ceil(steps - 1e-12) * tick
    return math.floor(steps + 1e-12) * tick
