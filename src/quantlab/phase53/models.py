"""Immutable evidence contracts for the Phase 53 human-execution decision."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class GateVerdict(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_TESTED = "NOT_TESTED"


class GoNoGoState(StrEnum):
    BLOCKED = "BLOCKED"
    EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
    READY_FOR_INDEPENDENT_REVIEW = "READY_FOR_INDEPENDENT_REVIEW"


class Phase53Gate(StrEnum):
    PRIOR_PHASE_ACCEPTANCE = "prior_phase_acceptance"
    SUSTAINED_OBSERVED_SHADOW = "sustained_observed_shadow"
    ZERO_BROKER_WRITE_AUDIT = "zero_broker_write_audit"
    DETERMINISTIC_REPLAY = "deterministic_replay"
    RECONCILIATION_CONTINUITY = "reconciliation_continuity"
    RESTART_RECOVERY = "restart_recovery"
    INDEPENDENT_VALIDATION = "independent_validation"
    HUMAN_AUTHORIZATION = "human_authorization"
    CERTIFIED_GATEWAY_DEPLOYMENT = "certified_gateway_deployment"
    SAFETY_WALL_PRESERVED = "safety_wall_preserved"


class Phase53Policy(BaseModel):
    """Evidence thresholds only; this policy has no execution controls."""

    model_config = ConfigDict(frozen=True)

    policy_version: str = "3.7.0-phase53"
    required_prior_phases: tuple[int, ...] = (49, 50, 51, 52)
    minimum_distinct_observed_sessions: int = Field(default=20, ge=2)
    minimum_observation_window_seconds: float = Field(default=1_209_600.0, gt=0.0)


class PriorPhaseAcceptanceEvidence(BaseModel):
    """References externally accepted prior-phase release evidence."""

    model_config = ConfigDict(frozen=True)

    accepted_phases: tuple[int, ...]
    release_references: tuple[str, ...]
    observed_at: datetime
    evidence_hash: str


class ZeroBrokerWriteAuditEvidence(BaseModel):
    """An independently exported, bounded audit—not an application assertion."""

    model_config = ConfigDict(frozen=True)

    audit_source: str
    audited_by: str
    window_start: datetime
    window_end: datetime
    broker_write_count: int = Field(ge=0)
    evidence_hash: str


class RestartRecoveryEvidence(BaseModel):
    """Evidence that an interrupted shadow workflow recovered without duplication."""

    model_config = ConfigDict(frozen=True)

    scenario_id: str
    verified_by: str
    observed_at: datetime
    recovered_without_duplicate_submission: bool
    evidence_hash: str


class IndependentValidationEvidence(BaseModel):
    """A separately attributable validation conclusion, not a self-attestation."""

    model_config = ConfigDict(frozen=True)

    report_id: str
    reviewer_id: str
    observed_at: datetime
    passed: bool
    evidence_hash: str


class GatewayDeploymentEvidence(BaseModel):
    """Deployment certification evidence only; never gateway configuration or credentials."""

    model_config = ConfigDict(frozen=True)

    deployment_id: str
    certification_id: str
    certified_by: str
    observed_at: datetime
    certified: bool
    evidence_hash: str


class Phase53EvidenceBundle(BaseModel):
    """All supplied Phase 53 evidence. Omitted evidence is deliberately NOT_TESTED."""

    model_config = ConfigDict(frozen=True)

    prior_phase_acceptance: PriorPhaseAcceptanceEvidence | None = None
    zero_broker_write_audit: ZeroBrokerWriteAuditEvidence | None = None
    restart_recovery: RestartRecoveryEvidence | None = None
    independent_validation: IndependentValidationEvidence | None = None
    gateway_deployment: GatewayDeploymentEvidence | None = None


class Phase53Check(BaseModel):
    model_config = ConfigDict(frozen=True)

    gate: Phase53Gate
    verdict: GateVerdict
    reason: str
    evidence_references: tuple[str, ...] = ()

    @property
    def blocks(self) -> bool:
        return self.verdict is not GateVerdict.PASS


class Phase53Readiness(BaseModel):
    """A dossier result, never an instruction or permission to submit an order."""

    model_config = ConfigDict(frozen=True)

    policy: Phase53Policy
    checks: tuple[Phase53Check, ...]
    state: GoNoGoState
    assessed_at: datetime
    dossier_hash: str
    live_trading: bool = False
    broker_write_enabled: bool = False
    execution_gateway_armed: bool = False
    note: str = (
        "READY_FOR_INDEPENDENT_REVIEW is not live-trading authorization. "
        "This dossier cannot arm or invoke a broker gateway."
    )
