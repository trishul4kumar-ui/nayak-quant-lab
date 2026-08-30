"""Latency is recorded, not invented from future quotes."""

from __future__ import annotations

from datetime import datetime

from quantlab.shadow.models import LatencyRecord, ShadowFill, ShadowOrder


def measure_latency(
    *,
    data_time: datetime,
    decision_time: datetime,
    orders: list[ShadowOrder],
    fills: list[ShadowFill],
) -> LatencyRecord:
    market_to_decision = max(0.0, (decision_time - data_time).total_seconds() * 1000.0)
    intent_to_order = 0.0
    order_to_fill = 0.0
    if orders and fills:
        first_arrival = min(item.arrival_time for item in orders)
        first_fill = min(item.fill_time for item in fills)
        order_to_fill = max(0.0, (first_fill - first_arrival).total_seconds() * 1000.0)
    return LatencyRecord(
        market_to_decision_ms=market_to_decision,
        decision_to_intent_ms=intent_to_order,
        intent_to_order_ms=intent_to_order,
        order_to_fill_ms=order_to_fill,
        total_cycle_ms=market_to_decision + order_to_fill,
        note="Recorded from frozen timestamps. Not live exchange clocks.",
    )
