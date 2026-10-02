"""Immutable real-time observations. Observe-only. Not signals."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class QualityStatus(StrEnum):
    VALID = "valid"
    DEGRADED = "degraded"
    STALE = "stale"
    INVALID = "invalid"
    MISSING = "missing"
    DISCONNECTED = "disconnected"
    UNKNOWN = "unknown"


class FreshnessStatus(StrEnum):
    FRESH = "fresh"
    STALE = "stale"
    UNKNOWN = "unknown"


class SequenceKind(StrEnum):
    VALID = "valid"
    GAP = "gap"
    OUT_OF_ORDER = "out_of_order"
    DUPLICATE = "duplicate"
    UNKNOWN = "unknown"


class SessionState(StrEnum):
    PRE_OPEN = "pre_open"
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"
    HALTED = "halted"
    UNKNOWN = "unknown"


class CorrectionStatus(StrEnum):
    NONE = "none"
    CORRECTED = "corrected"
    UNKNOWN = "unknown"


class MockFeedScenario(StrEnum):
    NORMAL = "normal"
    STALE = "stale"
    GAP = "gap"
    DUPLICATE = "duplicate"
    OUT_OF_ORDER = "out_of_order"
    MALFORMED = "malformed"
    DISCONNECT = "disconnect"
    CLOCK_DRIFT = "clock_drift"


class MarketObservation(BaseModel):
    model_config = ConfigDict(frozen=True)

    observation_id: str
    security_id: str
    venue: str
    source: str
    event_time: datetime
    exchange_time: datetime | None = None
    source_time: datetime | None = None
    receive_time: datetime
    processing_time: datetime
    decision_time: datetime | None = None
    sequence: int | None = None
    price: float | None = None
    quantity: float | None = None
    volume: float | None = None
    bid: float | None = None
    ask: float | None = None
    provenance: str = "mock-observe-only"
    schema_version: str = "3.1.0"
    payload_hash: str
    quality: QualityStatus = QualityStatus.UNKNOWN
    freshness: FreshnessStatus = FreshnessStatus.UNKNOWN
    correction: CorrectionStatus = CorrectionStatus.NONE
    live_trading: bool = False
    note: str = "Observation is not a signal and not an order."


class RealTimeSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    snapshot_id: str
    snapshot_hash: str
    source_manifest_hash: str
    security_master_hash: str
    calendar_version: str
    schema_version: str = "3.1.0"
    as_of: datetime
    observations: tuple[MarketObservation, ...]
    quality: QualityStatus
    freshness: FreshnessStatus
    session: SessionState
    sequence_kind: SequenceKind
    n_names: int
    extras: dict[str, Any] = Field(default_factory=dict)
    live_trading: bool = False
    note: str = "Frozen at T. Future appends cannot mutate this snapshot."

    def append_future_data(self, _future: object) -> RealTimeSnapshot:
        return self


class FeedHealth(BaseModel):
    model_config = ConfigDict(frozen=True)

    feed_connected: bool
    last_observation_time: datetime | None
    observation_age_ms: float | None
    sequence_health: SequenceKind
    clock_health: str
    data_quality: QualityStatus
    session_state: SessionState
    security_mapping_health: str
    snapshot_health: QualityStatus
    overall: str
    active_source: str | None = None
    source_priority: tuple[str, ...] = ()
    source_switches: tuple[str, ...] = ()
    coverage: float | None = None
    event_to_receive_ms: float | None = None
    receive_to_process_ms: float | None = None
    process_to_snapshot_ms: float | None = None
    corporate_action_state: str = "unknown"
    live_trading: bool = False
    write_enabled: bool = False
    note: str = "CONNECTED ≠ HEALTHY. UNKNOWN is never healthy."
