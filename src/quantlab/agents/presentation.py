"""Display-only DTOs; explicit fields prevent secrets and domain methods crossing Qt."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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
    adjudication: Literal["NOT_BUILT"] = "NOT_BUILT"


class AgentDeskPresentationService:
    def from_run(self, role: AgentRole, run: AgentRunRecord | None) -> AgentVisualStateDTO:
        return AgentVisualStateDTO(
            agent=role,
            state=run.state if run else AgentState.IDLE,
            task_label=run.state.value if run else "No active research run",
            completed_tools=len(run.tool_result_hashes) if run else 0,
        )
