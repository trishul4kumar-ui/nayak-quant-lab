"""Data freshness and PIT. Stale data cannot silently generate a trade."""

from __future__ import annotations

from datetime import datetime

from quantlab.core.errors import LookAheadError, StaleDataError
from quantlab.shadow.enums import StalePolicy
from quantlab.shadow.models import FreshnessRecord, ShadowConfig


def _ms(later: datetime, earlier: datetime) -> float:
    return max(0.0, (later - earlier).total_seconds() * 1000.0)


def evaluate_freshness(
    *,
    data_timestamp: datetime,
    received_timestamp: datetime,
    available_time: datetime,
    decision_time: datetime,
    processing_time: datetime,
    config: ShadowConfig,
    policy: StalePolicy = StalePolicy.ABSTAIN,
) -> FreshnessRecord:
    if available_time > decision_time:
        raise LookAheadError(
            "future_shadow_data: available_time > decision_time is future information"
        )
    age = _ms(decision_time, data_timestamp)
    skew = abs((received_timestamp - data_timestamp).total_seconds() * 1000.0)
    latency = _ms(processing_time, received_timestamp)
    stale = age > config.max_data_age_ms or skew > config.max_clock_skew_ms
    if stale and policy is StalePolicy.HALT:
        raise StaleDataError("stale market data cannot generate a trade decision")
    return FreshnessRecord(
        data_timestamp=data_timestamp,
        received_timestamp=received_timestamp,
        available_time=available_time,
        decision_time=decision_time,
        processing_time=processing_time,
        latency_ms=latency,
        age_ms=age,
        stale=stale,
        calendar_status="not_tested",
        note="STALE_DATA" if stale else "freshness recorded; synthetic seed is not REAL_MARKET",
    )
