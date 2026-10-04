"""Immutable trust, evidence, and run contracts. No prices/quantities in agent memos."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import AwareDatetime, Field, field_serializer, model_validator

from quantlab.agents.hashing import Artifact
from quantlab.ai.permissions import DENIED_CAPABILITIES, AiCapability


class AgentRole(StrEnum):
    BULL = "BULL"
    BEAR = "BEAR"


class AgentState(StrEnum):
    IDLE = "IDLE"
    OBSERVING = "OBSERVING"
    SCREENING = "SCREENING"
    FORMING_HYPOTHESIS = "FORMING_HYPOTHESIS"
    REQUESTING_EVIDENCE = "REQUESTING_EVIDENCE"
    ANALYZING = "ANALYZING"
    SELF_FALSIFYING = "SELF_FALSIFYING"
    WRITING_MEMO = "WRITING_MEMO"
    CRITIQUING = "CRITIQUING"
    REBUTTING = "REBUTTING"
    FROZEN = "FROZEN"
    NO_TRADE = "NO_TRADE"
    BLOCKED = "BLOCKED"
    STALE = "STALE"
    ERROR = "ERROR"


class ResearchMode(StrEnum):
    RESEARCH = "RESEARCH"
    REPLAY = "REPLAY"
    PAPER = "PAPER"
    SHADOW = "SHADOW"


class DataKind(StrEnum):
    SYNTHETIC = "SYNTHETIC"
    REAL = "REAL"


class EvidenceStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    UNKNOWN = "UNKNOWN"
    NOT_TESTED = "NOT_TESTED"


class AgentVersion(Artifact):
    version: str
    prompt_hash: str
    implementation_version: str = "39-v1"


class AgentIdentity(Artifact):
    agent_id: str
    role: AgentRole
    version: AgentVersion


class AgentModelIdentity(Artifact):
    provider: str
    model: str
    version: str


class VersionReference(Artifact):
    name: str
    version: str
    source_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


class AgentMandate(Artifact):
    role: AgentRole
    mandate: str
    granted: frozenset[AiCapability]
    max_tool_calls: int = Field(default=12, ge=1, le=50)

    @field_serializer("granted")
    def sorted_permissions(self, value: frozenset[AiCapability]) -> list[str]:
        return sorted(value)

    @model_validator(mode="after")
    def no_forbidden_grants(self) -> Self:
        if self.granted & DENIED_CAPABILITIES:
            raise ValueError("AI mandate contains permanently denied capabilities")
        return self


class AgentRunContext(Artifact):
    run_id: str
    parent_run_id: str | None = None
    as_of: AwareDatetime
    expires_at: AwareDatetime
    snapshot_id: str
    snapshot_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    snapshot_artifact_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    universe_id: str
    universe_version: str
    universe_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    security_scope: tuple[str, ...] = Field(min_length=1)
    data_kind: DataKind
    source_versions: tuple[VersionReference, ...]
    market_session: str
    agent: AgentIdentity
    model: AgentModelIdentity
    tool_policy_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    mode: ResearchMode = ResearchMode.RESEARCH
    history_hash: str | None = None

    @model_validator(mode="after")
    def temporal_boundary(self) -> Self:
        from quantlab.agents.hashing import digest

        if self.as_of > self.created_at or self.expires_at <= self.created_at:
            raise ValueError("invalid run time boundary")
        if tuple(sorted(set(self.security_scope))) != self.security_scope:
            raise ValueError("security scope must be sorted and unique")
        if digest(self.security_scope) != self.universe_hash:
            raise ValueError("universe hash mismatch")
        return self


class AgentUncertainty(Artifact):
    category: str
    description: str
    required_analysis: str | None = None


class EvidenceReference(Artifact):
    artifact_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    snapshot_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    kind: str
    status: EvidenceStatus
    available_time: AwareDatetime
    summary: str


class EvidenceMetric(Artifact):
    name: str
    security_id: str | None = None
    value: float | None = None
    unit: str = ""
    status: EvidenceStatus = EvidenceStatus.UNKNOWN
    available_time: AwareDatetime
    note: str = ""


class ResearchThesis(Artifact):
    hypothesis: str
    economic_rationale: str
    invalidation_conditions: tuple[str, ...] = Field(min_length=1)
    horizon: str


class Stance(StrEnum):
    LONG_CANDIDATE = "LONG_CANDIDATE"
    SHORT_CANDIDATE = "SHORT_CANDIDATE"
    AVOID = "AVOID"
    HEDGE = "HEDGE"
    HOLD = "HOLD"
    REDUCE = "REDUCE"
    EXIT = "EXIT"
    MORE_RESEARCH = "MORE_RESEARCH"
    NO_TRADE = "NO_TRADE"


class AgentResearchMemo(Artifact):
    thesis_id: str
    context_hash: str
    snapshot_hash: str
    as_of: AwareDatetime
    agent: AgentIdentity
    model_hash: str
    security_scope: tuple[str, ...]
    thesis: ResearchThesis
    evidence_for: tuple[EvidenceReference, ...]
    evidence_against: tuple[EvidenceReference, ...]
    requested_analyses: tuple[str, ...] = ()
    stance: Stance
    preferred_entry_archetype: str
    preferred_exposure: str
    raw_confidence: float = Field(ge=0, le=1)
    calibrated_confidence: float | None = None
    uncertainties: tuple[AgentUncertainty, ...]
    validation: EvidenceStatus = EvidenceStatus.NOT_TESTED
    no_trade_reason: str | None = None

    @model_validator(mode="after")
    def bound_evidence(self) -> Self:
        if self.calibrated_confidence is not None:
            raise ValueError("an agent cannot supply calibrated confidence")
        for ref in (*self.evidence_for, *self.evidence_against):
            if ref.snapshot_hash != self.snapshot_hash or ref.available_time > self.as_of:
                raise ValueError("memo evidence crosses the frozen boundary")
        if self.stance is Stance.NO_TRADE and not self.no_trade_reason:
            raise ValueError("NO_TRADE requires a reason")
        return self


class AgentRunRecord(Artifact):
    run_id: str
    context_hash: str
    state: AgentState
    prompt_hash: str
    model_hash: str
    tool_result_hashes: tuple[str, ...] = ()
    memo_hash: str | None = None
    duration_ms: float = Field(ge=0)
    error_code: str | None = None
