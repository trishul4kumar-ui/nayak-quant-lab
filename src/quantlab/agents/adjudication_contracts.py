"""Frozen host-owned adjudication inputs. No narrative, order or provider authority."""

from enum import StrEnum
from typing import Literal, Self

from pydantic import AwareDatetime, Field, model_validator

from quantlab.agents.contracts import AgentRole, DataKind, EvidenceStatus, ResearchMode
from quantlab.agents.debate_contracts import DebateStatus
from quantlab.agents.hashing import Artifact
from quantlab.agents.tool_contracts import ToolName
from quantlab.domain.research import CheckResult
from quantlab.research.gate import GateOutcome


class AdjudicationOutcome(StrEnum):
    BULL_DOMINANT = "BULL_DOMINANT"
    BEAR_DOMINANT = "BEAR_DOMINANT"
    CONFLICTED = "CONFLICTED"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    NO_EDGE = "NO_EDGE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    VALIDATION_BLOCKED = "VALIDATION_BLOCKED"
    RISK_BLOCKED = "RISK_BLOCKED"
    LIQUIDITY_BLOCKED = "LIQUIDITY_BLOCKED"
    NO_TRADE = "NO_TRADE"


class ComponentDefinition(Artifact):
    name: str
    metric: str
    lower: float
    upper: float
    weight: float = Field(ge=0, le=1)
    inverse: bool = False

    @model_validator(mode="after")
    def valid_range(self) -> Self:
        if self.upper <= self.lower:
            raise ValueError("component normalization range must be positive")
        return self


class AdjudicationPolicy(Artifact):
    policy_id: str
    required_evidence: tuple[str, ...]
    components: tuple[ComponentDefinition, ...]
    blocker_rules: tuple[str, ...]
    conflict_threshold: float = Field(ge=0, le=100)
    minimum_score: float = Field(ge=0, le=100)
    minimum_edge_bps: float = Field(ge=0)
    material_contradiction: float = Field(ge=0, le=1)
    minimum_liquidity: float = Field(ge=0, le=1)
    maximum_snapshot_age_seconds: int = Field(ge=1, le=300)

    @model_validator(mode="after")
    def coherent_weights(self) -> Self:
        names = [component.name for component in self.components]
        if len(names) != len(set(names)) or len(names) > 12:
            raise ValueError("unique bounded score components required")
        if abs(sum(component.weight for component in self.components) - 1) > 1e-9:
            raise ValueError("component weights must sum to one")
        if len(self.required_evidence) != len(set(self.required_evidence)):
            raise ValueError("duplicate required evidence")
        return self


class CanonicalMeasurement(Artifact):
    name: str
    canonical_tool: ToolName
    unit: str
    status: EvidenceStatus
    value: float | None = None
    result_hashes: tuple[str, ...]


class FrozenGateReason(Artifact):
    name: str
    result: CheckResult
    required: bool


class FrozenResearchGateEvidence(Artifact):
    outcome: GateOutcome | None
    reasons: tuple[FrozenGateReason, ...]
    measurement_hashes: tuple[str, ...]


class RoleAdjudicationEvidence(Artifact):
    role: AgentRole
    context_hash: str
    measurements: tuple[CanonicalMeasurement, ...]
    research_gate: FrozenResearchGateEvidence

    @model_validator(mode="after")
    def unique_names(self) -> Self:
        if len({row.name for row in self.measurements}) != len(self.measurements):
            raise ValueError("duplicate canonical measurements")
        return self


class FrozenAdjudicationInput(Artifact):
    transcript_hash: str
    bull_memo_hash: str
    bear_memo_hash: str
    boundary_hash: str
    snapshot_hash: str
    policy_hash: str
    as_of: AwareDatetime
    expires_at: AwareDatetime
    data_kind: DataKind
    mode: ResearchMode
    debate_status: DebateStatus
    data_quality: str
    data_freshness: str
    bull: RoleAdjudicationEvidence
    bear: RoleAdjudicationEvidence
    evidence_refs: tuple[str, ...]
    execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def role_and_clocks(self) -> Self:
        if self.bull.role is not AgentRole.BULL or self.bear.role is not AgentRole.BEAR:
            raise ValueError("both independent roles required")
        if self.created_at < self.as_of:
            raise ValueError("decision cannot predate evidence")
        return self


class ScoreComponent(Artifact):
    role: AgentRole
    name: str
    status: EvidenceStatus
    normalized_value: float | None = Field(default=None, ge=0, le=1)
    weight: float = Field(ge=0, le=1)
    points: float = Field(ge=0, le=100)
    evidence_refs: tuple[str, ...]


class AdjudicationDecision(Artifact):
    input_hash: str
    transcript_hash: str
    snapshot_hash: str
    policy_id: str
    policy_hash: str
    outcome: AdjudicationOutcome
    no_trade: bool
    bull_score: float = Field(ge=0, le=100)
    bear_score: float = Field(ge=0, le=100)
    score_components: tuple[ScoreComponent, ...]
    hard_blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    # Quantitative result identity excludes narrative and artifact lineage identities.
    result_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def non_execution(self) -> Self:
        dominant = self.outcome in {
            AdjudicationOutcome.BULL_DOMINANT,
            AdjudicationOutcome.BEAR_DOMINANT,
        }
        if self.no_trade == dominant or (self.hard_blockers and dominant):
            raise ValueError("blocked/non-dominant decisions must remain no trade")
        return self
