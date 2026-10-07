"""Hash-addressed candidate contracts. A candidate is never an order."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self

from pydantic import AwareDatetime, Field, model_validator

from quantlab.agents.contracts import EvidenceStatus
from quantlab.agents.hashing import Artifact, digest


class CandidateStatus(StrEnum):
    DRAFT = "DRAFT"
    GATHERING_EVIDENCE = "GATHERING_EVIDENCE"
    VALIDATING = "VALIDATING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    WATCH = "WATCH"
    PAPER_ELIGIBLE = "PAPER_ELIGIBLE"
    SHADOW_ELIGIBLE = "SHADOW_ELIGIBLE"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"


class ExposureStance(StrEnum):
    LONG = "LONG"
    BEARISH = "BEARISH"


class CandidatePolicy(Artifact):
    policy_id: str
    maximum_snapshot_age_seconds: int = Field(gt=0, le=86_400)
    maximum_price_deviation_bps: float = Field(gt=0, le=5_000)
    require_fresh_regime: bool = True
    require_liquidity: bool = True


class EvidenceSummary(Artifact):
    category: str = Field(min_length=1, max_length=80)
    status: EvidenceStatus
    evidence_refs: tuple[str, ...] = Field(min_length=1, max_length=24)
    summary: str = Field(min_length=1, max_length=600)


class CandidateBuildInput(Artifact):
    security_id: str = Field(min_length=1, max_length=160)
    stance: ExposureStance
    expires_at: AwareDatetime
    snapshot_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    bull_memo_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    bear_memo_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    debate_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    adjudication_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    level_plan_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    research_gate_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    research_gate_result: str = Field(min_length=1, max_length=80)
    raw_bull_confidence: float = Field(ge=0, le=1)
    raw_bear_confidence: float = Field(ge=0, le=1)
    calibrated_confidence: float | None = Field(default=None, ge=0, le=1)
    calibration_version: str | None = Field(default=None, max_length=120)
    summaries: tuple[EvidenceSummary, ...] = Field(min_length=6, max_length=16)
    data_quality: str = Field(min_length=1, max_length=80)
    data_freshness: str = Field(min_length=1, max_length=80)
    reference_price: float = Field(gt=0)
    reference_regime: str = Field(min_length=1, max_length=120)
    security_mapping_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    corporate_action_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def coherent_boundary(self) -> Self:
        if self.created_at >= self.expires_at:
            raise ValueError("candidate input is already expired")
        categories = [summary.category for summary in self.summaries]
        if len(categories) != len(set(categories)):
            raise ValueError("candidate evidence categories must be unique")
        if self.calibrated_confidence is not None and not self.calibration_version:
            raise ValueError("calibrated confidence requires a released version")
        return self


class TradeCandidatePacket(Artifact):
    candidate_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    candidate_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    status: CandidateStatus
    expires_at: AwareDatetime
    security_id: str
    stance: ExposureStance
    snapshot_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    bull_memo_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    bear_memo_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    debate_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    adjudication_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    level_plan_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    research_gate_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    research_gate_result: str
    summaries: tuple[EvidenceSummary, ...]
    data_quality: str
    data_freshness: str
    raw_bull_confidence: float = Field(ge=0, le=1)
    raw_bear_confidence: float = Field(ge=0, le=1)
    calibrated_confidence: float | None = Field(default=None, ge=0, le=1)
    calibration_version: str | None = None
    reference_price: float = Field(gt=0)
    reference_regime: str
    security_mapping_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    corporate_action_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    hard_blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    not_tested: tuple[str, ...]
    candidate_policy_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def status_matches_evidence(self) -> Self:
        if self.status is CandidateStatus.READY_FOR_REVIEW and (
            self.hard_blockers or self.data_quality != "valid" or self.data_freshness != "fresh"
        ):
            raise ValueError("only complete fresh candidates can be ready for review")
        semantic = {
            "candidate_id": self.candidate_id,
            "snapshot_hash": self.snapshot_hash,
            "adjudication_hash": self.adjudication_hash,
            "level_plan_hash": self.level_plan_hash,
            "policy": self.candidate_policy_hash,
        }
        if self.candidate_hash != digest(semantic):
            raise ValueError("candidate semantic hash mismatch")
        return self


class CandidateLifecycleEvent(Artifact):
    candidate_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    from_status: CandidateStatus
    to_status: CandidateStatus
    reason: str = Field(min_length=1, max_length=300)
    actor: Literal["SYSTEM", "HUMAN"]
    execution_authority: Literal[False] = False


class CandidateFreshnessInput(Artifact):
    candidate_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    current_price: float = Field(gt=0)
    current_regime: str = Field(min_length=1, max_length=120)
    current_spread_bps: float | None = Field(default=None, ge=0)
    liquidity_status: EvidenceStatus
    security_mapping_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    corporate_action_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    validation_expired: bool = False


class CandidateFreshness(Artifact):
    candidate_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    status: CandidateStatus
    reasons: tuple[str, ...]
    execution_authority: Literal[False] = False
