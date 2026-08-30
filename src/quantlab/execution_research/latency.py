"""Latency. Decision at T; eligible fill at T+Δt. No fill before arrival."""

from __future__ import annotations

from datetime import datetime

from quantlab.execution_research.definition import LatencyKind, MarketMicrostructureDefinition


def arrival_index(
    definition: MarketMicrostructureDefinition,
    decision_index: int,
    n_sessions: int,
    *,
    pre_arrival: bool = False,
    future_latency_sessions: int | None = None,
) -> int | None:
    if pre_arrival:
        return decision_index
    delay = definition.latency_sessions
    if definition.latency_model is LatencyKind.ZERO:
        delay = 0
    if future_latency_sessions is not None:
        delay = future_latency_sessions
    arrival = decision_index + max(int(delay), 0)
    if arrival >= n_sessions:
        return None
    return arrival


def no_pre_arrival(decision: datetime, arrival: datetime, fill_time: datetime) -> bool:
    return fill_time >= arrival and arrival >= decision
