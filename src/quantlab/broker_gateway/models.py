"""Immutable hashed broker snapshots. Read-only. Not live orders."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MockScenario(StrEnum):
    NORMAL = "normal"
    POSITION_MISMATCH = "position_mismatch"
    CASH_MISMATCH = "cash_mismatch"
    DUPLICATE_FILL = "duplicate_fill"
    ORPHAN_FILL = "orphan_fill"
    UNKNOWN_ORDER = "unknown_order"
    STALE_SNAPSHOT = "stale_snapshot"
    OUT_OF_ORDER = "out_of_order"
    MAPPING_AMBIGUITY = "mapping_ambiguity"
    PARTIAL_DATA = "partial_data"
    CONNECTION_FAILURE = "connection_failure"
    CREDENTIAL_FAILURE = "credential_failure"


class ReconStatus(StrEnum):
    RECONCILED = "reconciled"
    PARTIAL = "partial"
    MISMATCH = "mismatch"
    RECONCILIATION_REQUIRED = "reconciliation_required"
    BLOCKED = "blocked"


class Provenance(BaseModel):
    model_config = ConfigDict(frozen=True)

    adapter_id: str
    broker: str
    captured_at: datetime
    source_timestamp: datetime
    gateway_receipt_at: datetime
    source_sequence: int = 0
    schema_version: str = "2.8.0"
    note: str = "Broker provenance. Not a research observation."


class BrokerAccountSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    snapshot_id: str
    broker: str
    account_id_hash: str
    captured_at: datetime
    source_timestamp: datetime
    source_sequence: int
    schema_version: str
    payload_hash: str
    available_cash: float
    collateral: float
    utilized_margin: float
    available_margin: float
    equity: float | None = None
    buying_power: float | None = None
    live_trading: bool = False
    write_enabled: bool = False


class BrokerPositionSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    snapshot_id: str
    broker: str
    account_id_hash: str
    captured_at: datetime
    source_timestamp: datetime
    source_sequence: int
    schema_version: str
    payload_hash: str
    broker_instrument_id: str
    security_id: str
    exchange: str
    quantity: float
    average_price: float
    last_price: float | None = None
    realized_pnl: float | None = None
    unrealized_pnl: float | None = None
    product: str = "unknown"
    accounting_semantics: str = "ACCOUNTING_SEMANTICS_UNKNOWN"


class BrokerHoldingSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    snapshot_id: str
    broker: str
    account_id_hash: str
    captured_at: datetime
    source_timestamp: datetime
    source_sequence: int
    schema_version: str
    payload_hash: str
    broker_instrument_id: str
    security_id: str
    exchange: str
    quantity: float
    average_cost: float


class BrokerMarginSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    snapshot_id: str
    broker: str
    account_id_hash: str
    captured_at: datetime
    source_timestamp: datetime
    source_sequence: int
    schema_version: str
    payload_hash: str
    utilized_margin: float
    available_margin: float
    collateral: float
    settlement_semantics: str = "NOT_TESTED"


class BrokerOrderSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    snapshot_id: str
    broker: str
    account_id_hash: str
    captured_at: datetime
    source_timestamp: datetime
    source_sequence: int
    schema_version: str
    payload_hash: str
    broker_order_id: str
    status: str
    side: str
    quantity: float
    filled_quantity: float
    pending_quantity: float
    order_type: str
    price: float | None = None
    rejection_reason: str = ""
    broker_instrument_id: str = ""


class BrokerFillSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    snapshot_id: str
    broker: str
    account_id_hash: str
    captured_at: datetime
    source_timestamp: datetime
    source_sequence: int
    schema_version: str
    payload_hash: str
    broker_fill_id: str
    broker_order_id: str
    quantity: float
    price: float
    exchange: str
    charges: float | None = None


class InstrumentMapping(BaseModel):
    model_config = ConfigDict(frozen=True)

    broker_instrument_id: str
    security_id: str
    exchange: str
    trading_symbol: str
    display_symbol: str
    effective_from: datetime
    effective_to: datetime | None = None
    mapping_source: str
    mapping_confidence: str
    ambiguous: bool = False


class InternalBooks(BaseModel):
    model_config = ConfigDict(frozen=True)

    cash: float = 0.0
    reserved_cash: float = 0.0
    positions: tuple[tuple[str, float, float], ...] = ()
    orders: tuple[str, ...] = ()
    fills: tuple[str, ...] = ()


class ReconBreak(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: str
    instrument: str = ""
    broker_qty: float | None = None
    internal_qty: float | None = None
    delta_qty: float | None = None
    broker_cash: float | None = None
    internal_cash: float | None = None
    detail: str


class ReconResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    reconciliation_id: str
    status: ReconStatus
    captured_at: datetime
    breaks: tuple[ReconBreak, ...] = ()
    unknown_broker_orders: tuple[str, ...] = ()
    orphan_fills: tuple[str, ...] = ()
    missing_fills: tuple[str, ...] = ()
    payload_hash: str
    live_trading: bool = False
    write_enabled: bool = False
    note: str = "Differences are retained. Never silently repaired."


class GatewayIncident(BaseModel):
    model_config = ConfigDict(frozen=True)

    incident_id: str
    kind: str
    detail: str
    created_at: datetime = Field(default_factory=lambda: datetime(2024, 1, 2, tzinfo=UTC))


class BrokerHealth(BaseModel):
    model_config = ConfigDict(frozen=True)

    state: str
    healthy: bool
    stale: bool
    live_trading: bool = False
    write_enabled: bool = False
    broker_connected: bool = False
    credential_redacted: str = "***REDACTED***"
    note: str = "Read-only. Connection is not trading authorization."


class GatewaySnapshotBundle(BaseModel):
    model_config = ConfigDict(frozen=True)

    bundle_id: str
    connection_id: str
    adapter_id: str
    provenance: Provenance
    account: BrokerAccountSnapshot
    positions: tuple[BrokerPositionSnapshot, ...]
    holdings: tuple[BrokerHoldingSnapshot, ...]
    margins: BrokerMarginSnapshot
    orders: tuple[BrokerOrderSnapshot, ...]
    fills: tuple[BrokerFillSnapshot, ...]
    trades: tuple[BrokerFillSnapshot, ...]
    mappings: tuple[InstrumentMapping, ...]
    payload_hash: str
    extras: dict[str, Any] = Field(default_factory=dict)
    live_trading: bool = False
    write_enabled: bool = False
