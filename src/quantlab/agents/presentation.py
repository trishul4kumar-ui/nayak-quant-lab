"""Display-only DTOs; explicit fields prevent secrets and domain methods crossing Qt."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from quantlab.agents.adjudication_contracts import AdjudicationOutcome
from quantlab.agents.contracts import AgentRole, AgentRunRecord, AgentState
from quantlab.agents.debate_contracts import DebateStatus, EvidenceRelation


class SystemSafetyDTO(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    live_trading: Literal[False] = False
    ai_order_authority: Literal[False] = False
    mode: str = "RESEARCH"


class AgentVisualStateDTO(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    agent: AgentRole
    state: AgentState
    task_label: str
    completed_tools: int = Field(ge=0)
    raw_confidence: float | None = Field(default=None, ge=0, le=1)
    calibrated_confidence: float | None = Field(default=None, ge=0, le=1)


class EvidenceNodeSummaryDTO(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    artifact_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    label: str
    status: str


class EvidenceEdgeDTO(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    agent: AgentRole
    evidence_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    relation: EvidenceRelation


class DebateVisualDTO(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    transcript_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    status: DebateStatus
    critiques: int = Field(ge=0, le=2)
    rebuttals: int = Field(ge=0, le=2)
    edges: tuple[EvidenceEdgeDTO, ...] = Field(max_length=80)
    adjudication: Literal["NOT_EVALUATED"] = "NOT_EVALUATED"


class ComponentVisualDTO(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    role: AgentRole
    name: str
    status: str
    value: float | None = Field(default=None, ge=0, le=1)
    points: float = Field(ge=0, le=100)


class AdjudicationVisualDTO(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    decision_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    transcript_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    outcome: AdjudicationOutcome
    no_trade: bool
    bull_score: float = Field(ge=0, le=100)
    bear_score: float = Field(ge=0, le=100)
    blocker_count: int = Field(ge=0)
    expired: bool
    components: tuple[ComponentVisualDTO, ...] = Field(max_length=24)
    warnings: tuple[str, ...] = Field(max_length=20)
    execution_authority: Literal[False] = False


class AgentDeskPresentationService:
    def from_run(self, role: AgentRole, run: AgentRunRecord | None) -> AgentVisualStateDTO:
        return AgentVisualStateDTO(
            agent=role,
            state=run.state if run else AgentState.IDLE,
            task_label=run.state.value if run else "No active research run",
            completed_tools=len(run.tool_result_hashes) if run else 0,
        )
