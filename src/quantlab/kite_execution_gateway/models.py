"""Strict contracts for the separately deployed manual Kite gateway."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class SubmissionState(StrEnum):
    REJECTED = "REJECTED"
    SUBMITTING = "SUBMITTING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    SUBMISSION_UNKNOWN = "SUBMISSION_UNKNOWN"


class ManualLimitOrder(BaseModel):
    """A single immutable NSE cash-limit order. No defaulting or normalisation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    client_request_id: str = Field(min_length=8, max_length=128)
    idempotency_key: str = Field(min_length=16, max_length=128)
    account_fingerprint: str = Field(min_length=16, max_length=128)
    exchange: str
    tradingsymbol: str = Field(min_length=1, max_length=64)
    transaction_type: str
    quantity: int = Field(gt=0, le=100_000)
    product: str
    order_type: str
    price: float = Field(gt=0)
    validity: str
    created_at: datetime
    expires_at: datetime


class ManualOrderSubmission(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    order: ManualLimitOrder
    intent_hash: str = Field(min_length=64, max_length=64)
    confirmation_text: str = Field(min_length=72, max_length=80)
    totp_code: str = Field(pattern=r"^[0-9]{6}$")


class ManualOrderPreview(BaseModel):
    model_config = ConfigDict(frozen=True)

    intent_hash: str
    confirmation_text: str
    estimated_notional: float
    expires_at: datetime
    note: str = "Preview only. It has not contacted Kite and cannot place an order."


class ManualSubmissionResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    intent_hash: str
    idempotency_key: str
    state: SubmissionState
    attempted_at: datetime
    broker_order_id: str = ""
    detail: str = ""
