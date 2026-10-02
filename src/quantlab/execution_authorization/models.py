"""Immutable, hash-bound authorization governance contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class AuthorizationState(StrEnum):
    BLOCKED = "BLOCKED"
    INELIGIBLE = "INELIGIBLE"
    ELIGIBLE_FOR_HUMAN_REVIEW = "ELIGIBLE_FOR_HUMAN_REVIEW"
    HUMAN_AUTHORIZED = "HUMAN_AUTHORIZED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class CheckVerdict(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_TESTED = "NOT_TESTED"


class AuthorizationScope(BaseModel):
    model_config = ConfigDict(frozen=True)

    deployment_id: str
    broker_account_fingerprint: str
    allowed_security_ids: tuple[str, ...]
    universe_version: str
    strategy_hash: str
    model_hash: str
    portfolio_policy_hash: str
    release_id: str
    data_provider: str
    data_policy_hash: str
    risk_policy_hash: str
    max_gross_exposure: float | None
    max_notional: float | None
    max_turnover: float | None
    operating_mode: str
    session_start: datetime
    session_end: datetime
    expiry: datetime
    schema_version: str = "3.6.0"


class AuthorizationEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: str
    provenance: str
    observed_at: datetime
    expires_at: datetime | None = None
    content_hash: str
    report_id: str = ""


class AuthorizationCheck(BaseModel):
    model_config = ConfigDict(frozen=True)

    check_id: str
    result: CheckVerdict
    severity: str
    evidence: tuple[str, ...] = ()
    reason: str

    @property
    def blocks(self) -> bool:
        return self.severity == "critical" and self.result is not CheckVerdict.PASS


class AuthorizationPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    policy_version: str = "3.6.0"
    require_shadow_replay: bool = True
    require_complete_audit: bool = True
    max_evidence_age_seconds: float = 300.0


class AuthorizationAssessment(BaseModel):
    model_config = ConfigDict(frozen=True)

    assessment_id: str
    scope: AuthorizationScope
    policy: AuthorizationPolicy
    checks: tuple[AuthorizationCheck, ...]
    blockers: tuple[str, ...]
    evidence_hashes: tuple[str, ...]
    state: AuthorizationState
    assessed_at: datetime
    assessment_hash: str
    live_trading: bool = False
    broker_write_enabled: bool = False
    note: str = "Eligibility is not execution authorization and cannot place an order."


class HumanApprovalRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    approval_id: str
    assessment_id: str
    assessment_hash: str
    scope_hash: str
    approver_id: str
    approved_at: datetime
    expires_at: datetime
    confirmation: str
    state: AuthorizationState = AuthorizationState.HUMAN_AUTHORIZED
    approval_hash: str
    live_trading: bool = False


class AuthorizationRevocation(BaseModel):
    model_config = ConfigDict(frozen=True)

    revocation_id: str
    approval_id: str
    reason: str
    revoked_by: str
    revoked_at: datetime
    revocation_hash: str
