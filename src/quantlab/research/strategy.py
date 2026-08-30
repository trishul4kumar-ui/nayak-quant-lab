from datetime import datetime
from typing import Protocol, runtime_checkable

from quantlab.domain.models import OHLCVBar, Signal, StrategyContext, TargetPosition


@runtime_checkable
class Strategy(Protocol):
    """Broker-neutral strategy. No Kite, OpenAlgo, DB, UI, or LLM types."""

    def on_start(self, context: StrategyContext) -> None: ...

    def generate_signals(self, context: StrategyContext) -> list[Signal]: ...

    def target_positions(self, signals: list[Signal]) -> list[TargetPosition]: ...

    def on_stop(self, context: StrategyContext) -> None: ...


def closes_as_of(bars: list[OHLCVBar], as_of: datetime) -> list[OHLCVBar]:
    """Bars whose available_time <= as_of. Enforces PIT."""
    return [b for b in bars if b.pit.is_available_at(as_of)]
