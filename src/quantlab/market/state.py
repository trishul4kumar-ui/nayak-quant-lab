"""Build MarketState from bars available at as_of (ADR-010)."""

from __future__ import annotations

from datetime import datetime

from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import (
    LiquidityState,
    MarketState,
    OHLCVBar,
    PriceState,
    TrendState,
    VolatilityState,
)
from quantlab.math.metrics import log_returns, realized_vol, simple_returns


def build_market_state(
    series: list[OHLCVBar],
    as_of: datetime,
    lookback: int,
) -> MarketState | None:
    available = [b for b in series if b.pit.is_available_at(as_of)]
    available.sort(key=lambda b: b.pit.event_time)
    if not available:
        return None
    last = available[-1]
    prices = [b.close for b in available]
    rets = simple_returns(prices)
    log_rets = log_returns(prices) if all(p > 0 for p in prices) else []
    momentum: float | None = None
    if len(prices) >= lookback + 1 and prices[-1 - lookback] > 0:
        momentum = prices[-1] / prices[-1 - lookback] - 1.0
    vol = realized_vol(rets[-lookback:]) if lookback else realized_vol(rets)
    dollar = last.close * last.volume
    features: dict[str, float] = {}
    if momentum is not None:
        features[f"momentum_{lookback}"] = momentum
    if vol is not None:
        features[f"realized_vol_{lookback}"] = vol
    if rets:
        features["simple_return_1"] = rets[-1]
    return MarketState(
        instrument=last.instrument,
        as_of=as_of,
        pit=last.pit,
        price=PriceState(
            close=last.close,
            simple_return=rets[-1] if rets else None,
            log_return=log_rets[-1] if log_rets else None,
        ),
        volatility=VolatilityState(realized=vol),
        liquidity=LiquidityState(volume=last.volume, dollar_volume=dollar),
        trend=TrendState(momentum=momentum),
        features=features,
    )


def build_cross_section(
    bars_by_instrument: dict[InstrumentId, list[OHLCVBar]],
    as_of: datetime,
    lookback: int,
) -> list[MarketState]:
    states: list[MarketState] = []
    for series in bars_by_instrument.values():
        state = build_market_state(series, as_of, lookback)
        if state is not None:
            states.append(state)
    return states
