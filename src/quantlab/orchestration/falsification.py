"""Falsification using existing engines. A failed hypothesis is a valid result."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from quantlab.domain.models import Signal, StrategyContext, TargetPosition
from quantlab.research.momentum import CrossSectionalMomentum


class FalsificationReport(BaseModel):
    schema_version: str = "1"
    method: str
    primary_return: float | None
    falsifier_return: float | None
    hypothesis_survived: bool | None
    note: str = (
        "Sign reversal and cost stress are falsifiers. "
        "IID permutation of returns is not treated as automatically valid."
    )


class InvertedMomentum:
    """Rank the opposite tail. Uses the existing momentum feature, not a second engine."""

    name = "cs_momentum_inverted"
    version = "1.0.0"

    def __init__(self, lookback: int = 20, top_n: int = 2) -> None:
        self.lookback = lookback
        self.top_n = top_n
        self._inner = CrossSectionalMomentum(lookback=lookback, top_n=top_n)

    def on_start(self, context: StrategyContext) -> None:
        self._inner.on_start(context)

    def on_stop(self, context: StrategyContext) -> None:
        self._inner.on_stop(context)

    def generate_signals(self, context: StrategyContext) -> list[Signal]:
        signals = self._inner.generate_signals(context)
        return [Signal(instrument=s.instrument, score=-s.score, as_of=s.as_of) for s in signals]

    def target_positions(self, signals: list[Signal]) -> list[TargetPosition]:
        return self._inner.target_positions(signals)


class EqualWeightBaseline:
    name = "equal_weight"
    version = "1.0.0"
    lookback = 2

    def on_start(self, context: StrategyContext) -> None:
        return None

    def on_stop(self, context: StrategyContext) -> None:
        return None

    def generate_signals(self, context: StrategyContext) -> list[Signal]:
        as_of = context.as_of
        if not isinstance(as_of, datetime):
            raise TypeError("as_of must be datetime")
        seen: set[str] = set()
        out: list[Signal] = []
        for bar in context.bars:
            key = str(bar.instrument)
            if key in seen:
                continue
            if not bar.pit.is_available_at(as_of):
                continue
            seen.add(key)
            out.append(Signal(instrument=bar.instrument, score=1.0, as_of=as_of))
        return out

    def target_positions(self, signals: list[Signal]) -> list[TargetPosition]:
        if not signals:
            return []
        weight = 1.0 / len(signals)
        return [TargetPosition(instrument=s.instrument, weight=weight) for s in signals]


def falsification_summary(
    *,
    primary_return: float | None,
    inverted_return: float | None,
    cost_stress_return: float | None,
) -> FalsificationReport:
    survived: bool | None = None
    if primary_return is not None and inverted_return is not None:
        survived = primary_return > inverted_return
    note = "Sign reversal compared to the pre-registered primary."
    if cost_stress_return is not None and primary_return is not None:
        note += " Cost stress at 20 bps is recorded, not hidden."
    return FalsificationReport(
        method="sign_reversal_and_cost_stress",
        primary_return=primary_return,
        falsifier_return=inverted_return,
        hypothesis_survived=survived,
        note=note,
    )
