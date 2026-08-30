"""Strategy adapter: precomputed target weights for the existing next-bar engine."""

from __future__ import annotations

from datetime import datetime

from quantlab.domain.models import Signal, StrategyContext, TargetPosition


class WeightMapStrategy:
    """Looks up target weights by decision_time. Not an order generator."""

    name = "weight_map"
    version = "0.7.0"

    def __init__(self, weights_by_date: dict[datetime, list[TargetPosition]]) -> None:
        self._weights = weights_by_date

    def on_start(self, context: StrategyContext) -> None:
        return None

    def on_stop(self, context: StrategyContext) -> None:
        return None

    def generate_signals(self, context: StrategyContext) -> list[Signal]:
        targets = self._weights.get(context.as_of, [])
        return [
            Signal(instrument=t.instrument, score=t.weight, as_of=context.as_of) for t in targets
        ]

    def target_positions(self, signals: list[Signal]) -> list[TargetPosition]:
        return [TargetPosition(instrument=s.instrument, weight=s.score) for s in signals]
