"""Observation freshness. FRESH ≠ VALID."""

from __future__ import annotations

from datetime import datetime

from quantlab.realtime_data.models import FreshnessStatus, MarketObservation

DEFAULT_STALE_MS = 5_000.0


def age_ms(observation: MarketObservation, *, now: datetime) -> float:
    return (now - observation.receive_time).total_seconds() * 1000.0


def classify(
    observation: MarketObservation,
    *,
    now: datetime,
    stale_ms: float = DEFAULT_STALE_MS,
) -> FreshnessStatus:
    age = age_ms(observation, now=now)
    if age < 0:
        return FreshnessStatus.UNKNOWN
    if age > stale_ms:
        return FreshnessStatus.STALE
    return FreshnessStatus.FRESH
