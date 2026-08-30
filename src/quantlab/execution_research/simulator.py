"""Execution simulator around existing portfolio targets. Not a second backtester."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import OHLCVBar
from quantlab.domain.research import CheckResult
from quantlab.execution_research.definition import (
    ExecutionLeakFlags,
    MarketMicrostructureDefinition,
    OrderIntent,
    SimulatedFill,
)
from quantlab.execution_research.fills import simulate_fill
from quantlab.execution_research.intents import collect_weight_path, intents_from_path
from quantlab.execution_research.latency import arrival_index
from quantlab.execution_research.liquidity import liquidity_profile, series_for
from quantlab.execution_research.market import pit_close, trailing_vol, trailing_volume


class SimulationResult(BaseModel):
    schema_version: str = "1"
    model_id: str
    identity_hash: str
    fills: list[SimulatedFill] = Field(default_factory=list)
    n_intents: int = 0
    n_fills: int = 0
    n_partial: int = 0
    n_unfilled: int = 0
    total_cost: float = 0.0
    spread_cost: float = 0.0
    slippage_cost: float = 0.0
    impact_cost: float = 0.0
    explicit_cost: float = 0.0
    mean_fill_ratio: float = 0.0
    mean_participation: float | None = None
    capital: float = 1_000_000.0
    negative_cost: bool = False
    pre_arrival: bool = False
    note: str = (
        "Simulated fills overlay the existing next-bar backtester. This is not a second P&L engine."
    )


def simulate_execution(
    definition: MarketMicrostructureDefinition,
    bars: dict[InstrumentId, list[OHLCVBar]],
    *,
    capital: float = 1_000_000.0,
    lookback: int = 20,
    top_n: int = 2,
    leaks: ExecutionLeakFlags | None = None,
    intents: list[OrderIntent] | None = None,
) -> SimulationResult:
    flags = leaks or ExecutionLeakFlags()
    frozen = definition.identity_hash()
    calendar = _calendar(bars)
    if intents is None:
        path = collect_weight_path(bars, lookback=lookback, top_n=top_n)
        intents = intents_from_path(
            path, bars, capital=capital, max_participation=definition.max_participation
        )
    fills: list[SimulatedFill] = []
    for intent in intents:
        try:
            decision_index = calendar.index(intent.decision_time)
        except ValueError:
            continue
        future_delay = None
        if flags.future_latency and calendar:
            last_vol = float(next(iter(bars.values()))[-1].volume)
            future_delay = 2 if last_vol > 0 else 0
        arr_i = arrival_index(
            definition,
            decision_index,
            len(calendar),
            pre_arrival=flags.pre_arrival_fill,
            future_latency_sessions=future_delay,
        )
        if arr_i is None:
            continue
        arrival = calendar[arr_i]
        series = series_for(bars, intent.security_id)
        profile = liquidity_profile(
            series,
            security_id=intent.security_id,
            as_of=intent.decision_time if not flags.future_volume else arrival,
            max_participation=intent.max_participation,
            kind=definition.liquidity_model,
            lookback=definition.adv_lookback,
            use_future=flags.future_volume or flags.future_liquidity or flags.capacity_lookahead,
        )
        vol_as_of = arrival if flags.future_volume else intent.decision_time
        t_vol = trailing_vol(series, vol_as_of, definition.vol_lookback)
        t_adv = trailing_volume(series, vol_as_of, definition.adv_lookback)
        if flags.future_impact_parameter or flags.future_execution_parameter:
            t_vol = trailing_vol(series, calendar[-1], definition.vol_lookback)
        arrival_px = pit_close(series, arrival)
        future_spread = None
        if flags.future_spread and series:
            last = series[-1]
            if last.close > 0:
                future_spread = 10_000.0 * (last.high - last.low) / last.close
        fill = simulate_fill(
            intent,
            definition,
            arrival_time=arrival,
            arrival_price=arrival_px,
            volume=profile.session_volume,
            trailing_volume=t_adv,
            trailing_vol=t_vol,
            leaks=flags,
            future_spread_bps=future_spread,
        )
        fills.append(fill)

    mutated = flags.model_mutation
    parts_n = len([f for f in fills if f.fill_status.value == "partially_filled"])
    unfilled_n = len([f for f in fills if f.fill_status.value == "unfilled"])
    ratios = [f.fill_ratio for f in fills]
    parts_p = [f.participation for f in fills if f.participation is not None]
    total = sum(f.total_cost for f in fills)
    intent_times = {item.intent_id: item.decision_time for item in intents}
    pre_arrival = any(
        fill.arrival_time is not None and fill.arrival_time < intent_times[fill.intent_id]
        for fill in fills
        if fill.intent_id in intent_times
    )
    return SimulationResult(
        model_id=definition.definition_id,
        identity_hash=frozen,
        fills=fills,
        n_intents=len(intents),
        n_fills=len(fills),
        n_partial=parts_n,
        n_unfilled=unfilled_n,
        total_cost=total,
        spread_cost=sum(f.spread_cost for f in fills),
        slippage_cost=sum(f.slippage_cost for f in fills),
        impact_cost=sum(f.impact_cost for f in fills),
        explicit_cost=sum(f.explicit_cost for f in fills),
        mean_fill_ratio=sum(ratios) / len(ratios) if ratios else 0.0,
        mean_participation=sum(parts_p) / len(parts_p) if parts_p else None,
        capital=capital,
        negative_cost=any(f.total_cost < -1e-12 for f in fills),
        pre_arrival=pre_arrival,
        note=(
            "Simulated fills overlay the existing next-bar backtester. "
            f"mutation_flag={mutated}. status={CheckResult.WARN.value}."
        ),
    )


def _calendar(bars: dict[InstrumentId, list[OHLCVBar]]) -> list[datetime]:
    from quantlab.backtest.engine import shared_calendar

    return shared_calendar(bars)
