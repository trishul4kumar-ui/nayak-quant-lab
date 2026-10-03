"""Immutable reconciliation evidence and explicitly versioned comparison policy."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class ReconciliationStatus(StrEnum):
    MATCH = "MATCH"
    MATCH_WITH_TOLERANCE = "MATCH_WITH_TOLERANCE"
    MISMATCH = "MISMATCH"
    UNKNOWN = "UNKNOWN"
    STALE = "STALE"
    BROKER_UNAVAILABLE = "BROKER_UNAVAILABLE"
    INTERNAL_STATE_UNAVAILABLE = "INTERNAL_STATE_UNAVAILABLE"
    RECONCILIATION_BREAK = "RECONCILIATION_BREAK"


class OrderMatchStatus(StrEnum):
    MATCHED = "MATCHED"
    BROKER_ONLY = "BROKER_ONLY"
    INTERNAL_ONLY = "INTERNAL_ONLY"
    STATUS_MISMATCH = "STATUS_MISMATCH"
    QUANTITY_MISMATCH = "QUANTITY_MISMATCH"
    PRICE_MISMATCH = "PRICE_MISMATCH"
    TIMESTAMP_MISMATCH = "TIMESTAMP_MISMATCH"
    UNKNOWN = "UNKNOWN"


class ExceptionStatus(StrEnum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    INVESTIGATING = "INVESTIGATING"
    EXPLAINED = "EXPLAINED"
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"


class ReconciliationTolerances(BaseModel):
    """No implicit rounding: every permitted deviation is recorded in the report."""

    model_config = ConfigDict(frozen=True)

    policy_version: str = "3.3.0"
    quantity_absolute: float = 0.0
    price_absolute: float = 0.01
    cash_absolute: float = 0.01
    value_absolute: float = 0.01
    timestamp_seconds: float = 5.0
    max_broker_capture_window_seconds: float = 5.0


class InternalPosition(BaseModel):
    model_config = ConfigDict(frozen=True)

    security_id: str
    quantity: float
    average_price: float | None = None
    market_value: float | None = None
    realized_pnl: float | None = None


class InternalOrder(BaseModel):
    model_config = ConfigDict(frozen=True)

    broker_order_id: str
    status: str
    quantity: float
    price: float | None = None
    observed_at: datetime | None = None


class InternalFill(BaseModel):
    model_config = ConfigDict(frozen=True)

    broker_fill_id: str
    broker_order_id: str
    quantity: float
    price: float
    observed_at: datetime | None = None


class InternalAccountSnapshot(BaseModel):
    """A frozen internal-book view; it cannot be inferred from broker observations."""

    model_config = ConfigDict(frozen=True)

    snapshot_id: str
    account_id_hash: str
    observed_at: datetime
    available_cash: float | None = None
    utilized_margin: float | None = None
    available_margin: float | None = None
    holdings: tuple[InternalPosition, ...] = ()
    positions: tuple[InternalPosition, ...] = ()
    orders: tuple[InternalOrder, ...] = ()
    fills: tuple[InternalFill, ...] = ()


class ReconciliationException(BaseModel):
    """Original discrepancy fields remain immutable across workflow transitions."""

    model_config = ConfigDict(frozen=True)

    exception_id: str
    dimension: str
    key: str
    status: ExceptionStatus = ExceptionStatus.OPEN
    severity: str
    detail: str
    broker_value: str | None = None
    internal_value: str | None = None
    order_status: OrderMatchStatus | None = None
    created_at: datetime


class ReconciliationReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    reconciliation_id: str
    broker_snapshot_id: str | None
    internal_snapshot_id: str | None
    policy_version: str
    tolerances: ReconciliationTolerances
    status: ReconciliationStatus
    exceptions: tuple[ReconciliationException, ...] = ()
    reconciliation_hash: str
    observed_at: datetime
    matched_dimensions: tuple[str, ...] = ()
    tolerance_dimensions: tuple[str, ...] = ()
    live_trading: bool = False
    write_enabled: bool = False
    note: str = "Reconcile equals compare and record; it never creates compensating orders."
