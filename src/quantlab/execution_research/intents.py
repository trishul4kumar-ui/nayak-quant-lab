"""Portfolio targets → order intents. Intents are not sent to a broker."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import Instrument, OHLCVBar, Side, StrategyContext
from quantlab.execution_research.definition import OrderIntent
from quantlab.execution_research.market import pit_close
from quantlab.market.state import build_cross_section
from quantlab.portfolio.construction import construct_portfolio
from quantlab.research.momentum import CrossSectionalMomentum
from quantlab.research.strategy import Strategy
from quantlab.risk.firewall import RiskFirewall, RiskLimits


class WeightSnapshot(BaseModel):
    as_of: datetime
    weights: dict[str, float] = Field(default_factory=dict)


def collect_weight_path(
    bars: dict[InstrumentId, list[OHLCVBar]],
    *,
    lookback: int = 20,
    top_n: int = 2,
    strategy: Strategy | None = None,
    firewall: RiskFirewall | None = None,
) -> list[WeightSnapshot]:
    """Walk the session calendar through construct_portfolio. Does not apply returns."""
    strat = strategy or CrossSectionalMomentum(lookback=lookback, top_n=top_n)
    wall = firewall or RiskFirewall(RiskLimits(max_name_weight=0.55, max_names=5, max_gross=1.05))
    wall.register_instruments([Instrument(id=inst, name=inst.symbol, listed=True) for inst in bars])
    calendar = _calendar(bars)
    path: list[WeightSnapshot] = []
    for i in range(lookback + 1, len(calendar) - 1):
        as_of = calendar[i]
        context_bars: list[OHLCVBar] = []
        for series in bars.values():
            context_bars.extend(b for b in series if b.pit.is_available_at(as_of))
        states = build_cross_section(bars, as_of, lookback)
        ctx = StrategyContext(as_of=as_of, bars=context_bars, market_states=states)
        strat.on_start(ctx)
        signals = strat.generate_signals(ctx)
        proposal = construct_portfolio(strat, signals, as_of, reason="execution_research")
        authorized = wall.require(proposal)
        weights = {str(t.instrument): t.weight for t in authorized.targets}
        path.append(WeightSnapshot(as_of=as_of, weights=weights))
    return path


def intents_from_path(
    path: list[WeightSnapshot],
    bars: dict[InstrumentId, list[OHLCVBar]],
    *,
    capital: float,
    max_participation: float,
    strategy_id: str = "cs_momentum_v1",
) -> list[OrderIntent]:
    intents: list[OrderIntent] = []
    prev: dict[str, float] = {}
    names = {str(inst): inst for inst in bars}
    for i, snap in enumerate(path):
        names_now = set(prev) | set(snap.weights)
        for security in sorted(names_now):
            target = snap.weights.get(security, 0.0)
            current = prev.get(security, 0.0)
            delta = target - current
            if abs(delta) <= 1e-12:
                continue
            series = bars[names[security]] if security in names else []
            px = pit_close(series, snap.as_of)
            if px is None or px <= 0:
                continue
            qty = abs(delta) * capital / px
            side = Side.BUY if delta > 0 else Side.SELL
            intents.append(
                OrderIntent(
                    intent_id=f"intent:{i}:{security}:{side.value}",
                    decision_time=snap.as_of,
                    security_id=security,
                    side=side,
                    target_quantity=qty,
                    reference_price=px,
                    strategy_id=strategy_id,
                    max_participation=max_participation,
                )
            )
        prev = dict(snap.weights)
    return intents


def _calendar(bars: dict[InstrumentId, list[OHLCVBar]]) -> list[datetime]:
    from quantlab.backtest.engine import shared_calendar

    return shared_calendar(bars)
