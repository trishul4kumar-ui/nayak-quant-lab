"""Frozen certification identities. Material changes require a new candidate version."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from quantlab.certification.enums import (
    CertificationState,
    ChangeClass,
    ChecklistCode,
    ItemStatus,
    ReviewerRole,
    RiskCategory,
    RiskSeverity,
    SuspensionReason,
)


class Waiver(BaseModel):
    model_config = ConfigDict(frozen=True)

    waiver_id: str
    reason: str
    authority: str
    timestamp: datetime
    scope: str
    expiry: datetime
    note: str = "A waiver is not a PASS."


class ChecklistItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: ChecklistCode
    status: ItemStatus
    evidence_id: str = ""
    note: str = ""
    waiver: Waiver | None = None
    critical: bool = False


class ModelRiskAssessment(BaseModel):
    model_config = ConfigDict(frozen=True)

    category: RiskCategory
    severity: RiskSeverity = RiskSeverity.NOT_ASSESSED
    note: str = "No hidden default severity."


class Candidate(BaseModel):
    model_config = ConfigDict(frozen=True)

    candidate_id: str
    strategy_id: str = ""
    model_id: str = ""
    alpha_id: str = ""
    ensemble_id: str = ""
    portfolio_policy_id: str = ""
    capital_policy_id: str = ""
    risk_policy_id: str = ""
    paper_oms_policy_id: str = ""
    snapshot_id: str = "synthetic-diagnostic"
    feature_versions: dict[str, str] = Field(default_factory=dict)
    regime_definition: str = ""
    tca_policy_id: str = ""
    econometric_spec_id: str = ""
    family_id: str = ""
    knowledge_snapshot: str = ""
    software_version: str = ""
    config_hash: str = ""
    data_kind: str = "synthetic"
    claims_production_evidence: bool = False
    note: str = (
        "RESEARCH RESULT ≠ VALIDATED MODEL ≠ APPROVED STRATEGY "
        "≠ DEPLOYABLE STRATEGY ≠ LIVE ORDER AUTHORITY."
    )


class ReproductionResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    matched: bool
    expected_hash: str
    actual_hash: str
    environment: str = ""
    note: str = "Unexplained hash difference is a REPRODUCTION_BREAK."


class CertificationRun(BaseModel):
    model_config = ConfigDict(frozen=True)

    certification_id: str
    candidate_id: str
    state: CertificationState
    role: ReviewerRole
    as_of: datetime
    checklist_hash: str = ""
    evidence_hash: str = ""
    snapshot_hash: str = ""
    spec_hash: str = ""
    validation_hash: str = ""
    live_trading: bool = False
    note: str = "Certification is governance, not broker permission."


class CertificationRequest(BaseModel):
    candidate_id: str = "seed-candidate"
    role: ReviewerRole = ReviewerRole.RESEARCHER
    live_trading: bool = False
    data_kind: str = "synthetic"
    claims_production_evidence: bool = False
    ai_override: bool = False
    as_of: datetime = Field(default_factory=lambda: datetime(2024, 1, 15, tzinfo=UTC))
    checklist: list[ChecklistItem] | None = None
    target_state: CertificationState | None = None
    suspension_reason: SuspensionReason | None = None
    change_class: ChangeClass | None = None
    waiver: Waiver | None = None
    future_payload_ignored: dict[str, str] = Field(default_factory=dict)


class CertificationResult(BaseModel):
    run: CertificationRun
    candidate: Candidate
    state: CertificationState
    checklist: list[ChecklistItem] = Field(default_factory=list)
    risks: list[ModelRiskAssessment] = Field(default_factory=list)
    waivers: list[Waiver] = Field(default_factory=list)
    reproduction: ReproductionResult | None = None
    blocked: bool = False
    block_reasons: list[str] = Field(default_factory=list)
    live_trading: bool = False
    note: str = "CERTIFIED is not live. Prompt 05 remains the research gate."
