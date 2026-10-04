"""Append-only debate contracts; arguments never masquerade as canonical measurements."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self

from pydantic import AwareDatetime, Field, model_validator

from quantlab.agents.contracts import AgentRole, EvidenceStatus
from quantlab.agents.hashing import Artifact
from quantlab.agents.research import AnalysisRequest, Draft
from quantlab.agents.tool_contracts import ToolName


class DebateStatus(StrEnum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    STALE = "STALE"


class CritiqueDraft(Draft):
    critic_agent: AgentRole
    target_memo_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    claims_challenged: tuple[str, ...] = Field(min_length=1, max_length=8)
    evidence_conflicts: tuple[str, ...] = Field(max_length=8)
    missing_tests: tuple[str, ...] = Field(max_length=10)
    alternative_explanations: tuple[str, ...] = Field(min_length=1, max_length=8)
    factor_objections: tuple[str, ...] = Field(max_length=8)
    regime_objections: tuple[str, ...] = Field(max_length=8)
    cost_liquidity_objections: tuple[str, ...] = Field(max_length=8)
    invalidation_evidence: tuple[str, ...] = Field(max_length=8)
    unsupported_claims: tuple[str, ...] = Field(max_length=8)
    severity: Literal["INFO", "WARN", "CRITICAL"]
    critic_confidence: float = Field(ge=0, le=1)
    evidence_refs: tuple[str, ...] = Field(max_length=24)
    requests: tuple[AnalysisRequest, ...] = Field(max_length=3)

    @model_validator(mode="after")
    def bounded_text(self) -> Self:
        if len(self.model_dump_json()) > 16000:
            raise ValueError("critique text budget exceeded")
        return self


class RebuttalDraft(Draft):
    respondent_agent: AgentRole
    target_critique_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    responses: tuple[str, ...] = Field(min_length=1, max_length=8)
    concessions: tuple[str, ...] = Field(max_length=8)
    unresolved_questions: tuple[str, ...] = Field(max_length=8)
    evidence_refs: tuple[str, ...] = Field(max_length=24)

    @model_validator(mode="after")
    def bounded_text(self) -> Self:
        if len(self.model_dump_json()) > 10000:
            raise ValueError("rebuttal text budget exceeded")
        return self


class DebateProtocol(Artifact):
    version: Literal["42-v1"] = "42-v1"
    initial_memos_per_role: Literal[1] = 1
    critiques_per_role: Literal[1] = 1
    rebuttals_per_role: Literal[1] = 1
    tool_attempts_per_role: Literal[3] = 3
    model_timeout_seconds: Literal[30] = 30
    max_evidence_characters: Literal[48000] = 48000
    schema_retries: Literal[1] = 1


class DebateSession(Artifact):
    debate_id: str
    protocol_hash: str
    boundary_hash: str
    snapshot_hash: str
    as_of: AwareDatetime
    expires_at: AwareDatetime
    bull_memo_hash: str
    bear_memo_hash: str
    bull_context_hash: str
    bear_context_hash: str
    include_rebuttals: bool


class FrozenCritique(Artifact):
    debate_id: str
    snapshot_hash: str
    context_hash: str
    prompt_hash: str
    model_hash: str
    duration_ms: float = Field(ge=0)
    draft: CritiqueDraft
    tool_result_hashes: tuple[str, ...]
    quantitative_authority: Literal[False] = False


class FrozenRebuttal(Artifact):
    debate_id: str
    snapshot_hash: str
    context_hash: str
    prompt_hash: str
    model_hash: str
    duration_ms: float = Field(ge=0)
    draft: RebuttalDraft
    quantitative_authority: Literal[False] = False


class EvidenceRelation(StrEnum):
    SUPPORT = "SUPPORT"
    CONTRADICTION = "CONTRADICTION"
    CRITIQUE_REFERENCE = "CRITIQUE_REFERENCE"
    REQUESTED = "REQUESTED"


class EvidenceGraphEdge(Artifact):
    agent: AgentRole
    evidence_hash: str
    relation: EvidenceRelation
    interpretation_verified: Literal[False] = False


class FalsificationCheck(Artifact):
    name: str
    canonical_tool: ToolName
    result_hashes: tuple[str, ...]
    status: EvidenceStatus
    note: str


class DebateTranscript(Artifact):
    debate_id: str
    session_hash: str
    protocol_hash: str
    boundary_hash: str
    snapshot_hash: str
    bull_memo_hash: str
    bear_memo_hash: str
    critiques: tuple[str, ...]
    rebuttals: tuple[str, ...]
    evidence_hashes: tuple[str, ...]
    evidence_graph: tuple[EvidenceGraphEdge, ...]
    falsification_checks: tuple[FalsificationCheck, ...]
    started_at: AwareDatetime
    completed_at: AwareDatetime
    status: DebateStatus
    error_code: str | None = None
    execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def finite_protocol(self) -> Self:
        if len(self.critiques) > 2 or len(self.rebuttals) > 2:
            raise ValueError("recursive debate forbidden")
        if self.status is DebateStatus.COMPLETE and len(self.critiques) != 2:
            raise ValueError("complete debate requires both real critiques")
        if self.completed_at < self.started_at:
            raise ValueError("invalid debate clocks")
        return self
