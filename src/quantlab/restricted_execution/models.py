"""Immutable contracts for one-attempt restricted execution submission."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class RequestAction(StrEnum):
    SUBMIT = "SUBMIT"
    CANCEL = "CANCEL"


class ExecutionState(StrEnum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    AWAITING_HUMAN_CONFIRMATION = "AWAITING_HUMAN_CONFIRMATION"
    CONFIRMED = "CONFIRMED"
    SUBMITTING = "SUBMITTING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    REJECTED = "REJECTED"
    SUBMISSION_UNKNOWN = "SUBMISSION_UNKNOWN"
    RECONCILED = "RECONCILED"


class GatewayOrderIntent(BaseModel):
    """Exact broker-neutral payload. Values are never normalised or substituted."""

    model_config = ConfigDict(frozen=True)

    request_id: str
    action: RequestAction = RequestAction.SUBMIT
    account_fingerprint: str
    security_id: str
    side: str
    quantity: float
    order_type: str
    limit_price: float | None = None
    broker_order_id: str = ""
    created_at: datetime
    expires_at: datetime
    idempotency_key: str
    note: str = "Pre-approved intent only; this object cannot generate a trade."


class ExecutionEnvelope(BaseModel):
    model_config = ConfigDict(frozen=True)

    intent: GatewayOrderIntent
    approval_id: str
    assessment_hash: str
    scope_hash: str
    envelope_hash: str
    created_at: datetime
    state: ExecutionState = ExecutionState.DRAFT
    validation_errors: tuple[str, ...] = ()
    note: str = "Hash-bound restricted execution envelope. No broker routing is implied."


class HumanConfirmation(BaseModel):
    model_config = ConfigDict(frozen=True)

    envelope_hash: str
    actor_id: str
    confirmation: str
    confirmed_at: datetime
    expires_at: datetime


class ExecutionValidationContext(BaseModel):
    """Fresh, read-only control-plane evidence required immediately before submit."""

    model_config = ConfigDict(frozen=True)

    market_price: float | None = None
    market_data_healthy: bool = False
    broker_snapshot_fresh: bool = False
    reconciliation_acceptable: bool = False
    release_valid: bool = False
    authorization_evidence_fresh: bool = False
    account_equity: float | None = None
    available_cash: float | None = None
    available_margin: float | None = None
    current_gross_exposure: float | None = None
    projected_turnover: float | None = None
    observed_at: datetime | None = None
    note: str = "Unknown control-plane state blocks restricted execution."


class GatewaySubmission(BaseModel):
    model_config = ConfigDict(frozen=True)

    envelope_hash: str
    state: ExecutionState
    attempted_at: datetime
    correlation_id: str
    broker_order_id: str = ""
    detail: str = ""
    attempt_count: int = Field(default=0, ge=0, le=1)
    reconciled_at: datetime | None = None
