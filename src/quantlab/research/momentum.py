"""Cross-sectional momentum: close[t] / close[t-lookback] - 1 using available data only."""

from __future__ import annotations

from datetime import datetime

from quantlab.core.errors import LookAheadError
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import OHLCVBar, Signal, StrategyContext, TargetPosition
from quantlab.research.strategy import closes_as_of


class CrossSectionalMomentum:
    """Deterministic first strategy. Validates architecture, not returns."""

    name = "cs_momentum_v1"
    version = "0.1.0"

    def __init__(self, lookback: int = 20, top_n: int = 2) -> None:
        if lookback < 2:
            raise ValueError("lookback must be >= 2")
        self.lookback = lookback
        self.top_n = top_n

    def on_start(self, context: StrategyContext) -> None:
        return None

    def on_stop(self, context: StrategyContext) -> None:
        return None

    def generate_signals(self, context: StrategyContext) -> list[Signal]:
        as_of = _as_datetime(context.as_of)
        if context.market_states:
            signals: list[Signal] = []
            key = f"momentum_{self.lookback}"
            for state in context.market_states:
                if not state.pit.is_available_at(as_of):
                    raise LookAheadError(f"feature used future state for {state.instrument}")
                score = state.features.get(key)
                if score is None:
                    continue
                signals.append(Signal(instrument=state.instrument, score=score, as_of=as_of))
            return signals
        by_inst: dict[InstrumentId, list[OHLCVBar]] = {}
        for bar in closes_as_of(context.bars, as_of):
            by_inst.setdefault(bar.instrument, []).append(bar)

        fallback: list[Signal] = []
        for instrument, series in by_inst.items():
            series.sort(key=lambda b: b.pit.event_time)
            if len(series) < self.lookback + 1:
                continue
            last = series[-1]
            past = series[-1 - self.lookback]
            if last.pit.available_time > as_of or past.pit.available_time > as_of:
                raise LookAheadError(f"feature used future bar for {instrument}")
            if past.close <= 0:
                continue
            score = last.close / past.close - 1.0
            fallback.append(Signal(instrument=instrument, score=score, as_of=as_of))
        return fallback

    def target_positions(self, signals: list[Signal]) -> list[TargetPosition]:
        ranked = sorted(signals, key=lambda s: s.score, reverse=True)
        winners = [s for s in ranked if s.score > 0][: self.top_n]
        if not winners:
            return []
        weight = 1.0 / len(winners)
        return [TargetPosition(instrument=s.instrument, weight=weight) for s in winners]


def _as_datetime(value: object) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("as_of must be datetime")
    return value
