"""Immutable live-certification identities. CERTIFIED is not live."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from quantlab.release.state import CertState


class ActorKind(StrEnum):
    RESEARCHER = "researcher"
    VALIDATOR = "validator"
    OPERATIONS = "operations"
    RELEASE_AUTHORITY = "release_authority"
    AI_SUGGESTION = "ai_suggestion"
    SYSTEM = "system"


class CriterionVerdict(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    NOT_TESTED = "not_tested"
    WAIVED = "waived"
    NOT_APPLICABLE = "not_applicable"


class ReleaseStage(StrEnum):
    RESEARCH = "research"
    PAPER = "paper"
    SHADOW = "shadow"
    RESTRICTED_LIVE = "restricted_live"
    EXPANDED_LIVE = "expanded_live"


class CriterionResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    criterion_id: str
    domain: str
    verdict: CriterionVerdict
    reason: str
    critical: bool = True

    @property
    def blocks(self) -> bool:
        if self.verdict is CriterionVerdict.FAIL and self.critical:
            return True
        return bool(self.critical and self.verdict is CriterionVerdict.NOT_TESTED)


class WaiverRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    waiver_id: str
    criterion_id: str
    reason: str
    risk_statement: str
    authority: str
    scope: str
    created_at: datetime
    expires_at: datetime
    mitigation: str
    actor: ActorKind = ActorKind.RELEASE_AUTHORITY


class CertificationRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    package_id: str = "LIVE-CERT-001"
    as_of: datetime = datetime(2024, 1, 2, tzinfo=UTC)
    owner_id: str = "researcher-1"
    validator_id: str = ""
    data_kind: str = "synthetic"
    intended_stage: ReleaseStage = ReleaseStage.RESEARCH
    research_ok: bool = False
    statistical_ok: bool = False
    data_ok: bool = False
    execution_ok: bool = False
    paper_shadow_ok: bool = False
    risk_ok: bool = False
    safety_fail: bool = False
    ops_ok: bool = False
    independent_validation: bool = False
    recon_break: bool = False
    synthetic_as_production: bool = False
    model_mutated: bool = False
    config_mutated: bool = False
    expired: bool = False
    ai_override: bool = False
    actor: ActorKind = ActorKind.SYSTEM
    human_approver_id: str = ""
    human_role: ActorKind = ActorKind.SYSTEM
    max_capital: float = 0.0
    spec_hash: str = "spec-v1"
    note: str = "Live-certification request. CERTIFIED is not live."


class CertificationPackage(BaseModel):
    model_config = ConfigDict(frozen=True)

    package_id: str
    spec_hash: str
    evidence_hash: str
    software_version: str
    data_kind: str
    intended_stage: ReleaseStage
    owner_id: str
    validator_id: str
    created_at: datetime
    expires_at: datetime
    package_hash: str
    live_trading: bool = False
    note: str = "Immutable certification package. Not broker-connected."


class ReleaseManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    release_id: str
    certification_id: str
    software_version: str
    git_commit: str
    configuration_hash: str
    research_snapshot_hash: str
    data_snapshot_hash: str
    model_hash: str
    ensemble_hash: str
    portfolio_policy_hash: str
    risk_policy_hash: str
    execution_policy_hash: str
    safety_policy_hash: str
    ops_health_hash: str
    capital_limit: float
    release_stage: ReleaseStage
    expiry: datetime
    approved_by: str
    validator: str
    timestamp: datetime
    manifest_hash: str
    live_trading: bool = False
    live_enabled: bool = False


class CertificationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    evaluation_id: str
    state: CertState
    package: CertificationPackage | None = None
    manifest: ReleaseManifest | None = None
    criteria: tuple[CriterionResult, ...] = ()
    live_trading: bool = False
    live_enabled: bool = False
    broker_connected: bool = False
    blocked: bool = True
    extras: dict[str, Any] = Field(default_factory=dict)
    result_hash: str = ""
    note: str = "Certification proves readiness. It does not create permission to trade."

    def criterion(self, criterion_id: str) -> CriterionResult | None:
        for item in self.criteria:
            if item.criterion_id == criterion_id:
                return item
        return None
