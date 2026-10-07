"""Deterministic, caller-driven tick replay with explicit gap/latency injection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from quantlab.intraday_research.models import ArrivalState, TickObservation


@dataclass(frozen=True)
class ReplayPolicy:
    latency_ms: int = 0
    inject_gap_after: int | None = None


def replay(
    ticks: tuple[TickObservation, ...], policy: ReplayPolicy | None = None
) -> tuple[TickObservation, ...]:
    """Replay never reads future ticks; injected conditions become explicit artifacts."""
    policy = policy or ReplayPolicy()
    emitted: list[TickObservation] = []
    for index, tick in enumerate(ticks):
        tick = tick.verified()
        state = ArrivalState.GAP if policy.inject_gap_after == index else tick.arrival_state
        payload = tick.model_dump(mode="python", exclude={"content_hash"})
        payload["arrival_state"] = state
        payload["processed_at"] = tick.processed_at + timedelta(milliseconds=policy.latency_ms)
        emitted.append(TickObservation.model_validate(payload))
    return tuple(emitted)
