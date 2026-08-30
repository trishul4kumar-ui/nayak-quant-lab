"""Buy-and-hold, equal-weight, and seeded random baselines."""

from __future__ import annotations

import hashlib

from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import Signal, StrategyContext, TargetPosition


class EqualWeightBaseline:
    name = "equal_weight_v1"
    version = "0.1.0"

    def on_start(self, context: StrategyContext) -> None:
        return None

    def on_stop(self, context: StrategyContext) -> None:
        return None

    def generate_signals(self, context: StrategyContext) -> list[Signal]:
        seen: dict[str, Signal] = {}
        for bar in context.bars:
            if bar.pit.is_available_at(context.as_of):
                seen[str(bar.instrument)] = Signal(
                    instrument=bar.instrument, score=1.0, as_of=context.as_of
                )
        return list(seen.values())

    def target_positions(self, signals: list[Signal]) -> list[TargetPosition]:
        if not signals:
            return []
        weight = 1.0 / len(signals)
        return [TargetPosition(instrument=s.instrument, weight=weight) for s in signals]


class BuyAndHoldBaseline(EqualWeightBaseline):
    """Constant long the universe. Same weights every day in a static synthetic set."""

    name = "buy_and_hold_v1"
    version = "0.1.0"


class RandomSignalBaseline:
    """Deterministic pseudo-random scores. Seed is part of the experiment identity."""

    name = "random_signal_v1"
    version = "0.1.0"

    def __init__(self, seed: int = 0, top_n: int = 2) -> None:
        self.seed = seed
        self.top_n = top_n

    def on_start(self, context: StrategyContext) -> None:
        return None

    def on_stop(self, context: StrategyContext) -> None:
        return None

    def generate_signals(self, context: StrategyContext) -> list[Signal]:
        instruments: list[InstrumentId] = []
        if context.market_states:
            instruments = [state.instrument for state in context.market_states]
        else:
            seen: dict[str, InstrumentId] = {}
            for bar in context.bars:
                if bar.pit.is_available_at(context.as_of):
                    seen[str(bar.instrument)] = bar.instrument
            instruments = list(seen.values())
        out: list[Signal] = []
        for inst in instruments:
            digest = hashlib.sha256(
                f"{self.seed}:{context.as_of.isoformat()}:{inst}".encode()
            ).digest()
            score = int.from_bytes(digest[:8], "big") / float(2**64)
            out.append(Signal(instrument=inst, score=score, as_of=context.as_of))
        return out

    def target_positions(self, signals: list[Signal]) -> list[TargetPosition]:
        ranked = sorted(signals, key=lambda s: s.score, reverse=True)[: self.top_n]
        if not ranked:
            return []
        weight = 1.0 / len(ranked)
        return [TargetPosition(instrument=s.instrument, weight=weight) for s in ranked]
