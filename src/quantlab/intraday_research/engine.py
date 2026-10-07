"""Pure tick-to-signal calculation. This module imports no agent/provider/broker path."""

from datetime import datetime
from typing import Literal

from quantlab.intraday_research.models import (
    ArrivalState,
    MicrostructureSnapshot,
    ScalpSignal,
    ScalpStrategyDefinition,
    TickObservation,
)


def features(tick: TickObservation) -> MicrostructureSnapshot:
    tick = tick.verified()
    if tick.depth is None:
        return MicrostructureSnapshot(
            created_at=tick.processed_at,
            schema_version="intraday-research-v1",
            tick_hash=tick.content_hash,
            quality=ArrivalState.MISSING_DEPTH,
        )
    bid, ask = tick.depth.bids[0], tick.depth.asks[0]
    total = bid.quantity + ask.quantity
    imbalance = (bid.quantity - ask.quantity) / total if total else 0.0
    microprice = (ask.price * bid.quantity + bid.price * ask.quantity) / total if total else None
    mid = (bid.price + ask.price) / 2
    return MicrostructureSnapshot(
        created_at=tick.processed_at,
        schema_version="intraday-research-v1",
        tick_hash=tick.content_hash,
        spread=ask.price - bid.price,
        relative_spread_bps=(ask.price - bid.price) / mid * 10_000,
        microprice=microprice,
        top_imbalance=imbalance,
        quality=tick.arrival_state,
    )


def evaluate_signal(
    tick: TickObservation, strategy: ScalpStrategyDefinition, *, now: datetime
) -> ScalpSignal:
    """Fail closed on stale/invalid data, missing depth, or an absent cost model."""
    strategy = strategy.verified()
    frame = features(tick)
    valid = frame.quality is ArrivalState.VALID
    fresh = (now - tick.processed_at).total_seconds() <= strategy.horizon_seconds
    spread_ok = (frame.relative_spread_bps or float("inf")) <= strategy.maximum_spread_bps
    direction: Literal["LONG", "BEARISH", "ABSTAIN"] = "ABSTAIN"
    reason = "DATA_QUALITY_BLOCK"
    if valid and fresh and spread_ok:
        imbalance = frame.top_imbalance or 0.0
        if imbalance >= strategy.entry_threshold:
            direction, reason = "LONG", "TOP_OF_BOOK_IMBALANCE"
        elif imbalance <= -strategy.entry_threshold:
            direction, reason = "BEARISH", "TOP_OF_BOOK_IMBALANCE"
        else:
            reason = "NO_DETERMINISTIC_EDGE"
    elif not fresh:
        reason = "STALE_FEED"
    elif not spread_ok:
        reason = "SPREAD_LIMIT"
    return ScalpSignal(
        created_at=now,
        schema_version="intraday-research-v1",
        strategy_hash=strategy.content_hash,
        snapshot_hash=frame.content_hash,
        direction=direction,
        reason=reason,
        quality=frame.quality,
    )
