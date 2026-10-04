"""Bounded analyst drafts and durable research-only lifecycle contracts."""

from __future__ import annotations

import json
import re
from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from quantlab.agents.contracts import AgentResearchMemo, AgentState, EvidenceStatus
from quantlab.agents.hashing import Artifact, reject_sensitive_payload, safe_text
from quantlab.agents.tool_contracts import ToolName


class Draft(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    @model_validator(mode="after")
    def research_only(self) -> Self:
        payload = self.model_dump(mode="json")
        reject_sensitive_payload(payload)
        text = json.dumps(payload)
        if safe_text(text) != text or re.search(
            r"(?:₹\s*\d|\bINR\s*\d|\b(?:buy|sell)\s+\d|"
            r"\b(?:quantity|qty|entry|stop|target|order[_ ]?price)\s*[:=@]\s*\d)",
            text,
            re.IGNORECASE,
        ):
            raise ValueError("execution levels, sizing and secrets are forbidden")
        return self


class EntryArchetype(StrEnum):
    BREAKOUT = "BREAKOUT"
    PULLBACK = "PULLBACK"
    LIMIT_ZONE = "LIMIT_ZONE"
    MOMENTUM_CONTINUATION = "MOMENTUM_CONTINUATION"
    MEAN_REVERSION_RECOVERY = "MEAN_REVERSION_RECOVERY"
    MORE_RESEARCH = "MORE_RESEARCH"


class ExitArchetype(StrEnum):
    THESIS_INVALIDATION = "THESIS_INVALIDATION"
    MOMENTUM_DECAY = "MOMENTUM_DECAY"
    REGIME_CHANGE = "REGIME_CHANGE"
    TIME_REVIEW = "TIME_REVIEW"
    MORE_RESEARCH = "MORE_RESEARCH"


class CheckQuestion(StrEnum):
    CONTRADICTION = "CONTRADICTION"
    FALSIFICATION = "FALSIFICATION"
    FACTOR_EXPLANATION = "FACTOR_EXPLANATION"
    COST_SURVIVAL = "COST_SURVIVAL"
    OOS_SURVIVAL = "OOS_SURVIVAL"
    REGIME_SPECIFICITY = "REGIME_SPECIFICITY"
    MISSING_DATA = "MISSING_DATA"


class AnalysisRequest(Draft):
    tool: ToolName
    analysis_id: str | None = Field(max_length=80)
    security_id: str | None = Field(max_length=80)
    lookback: int = Field(ge=2, le=252)


class ResearchPlan(Draft):
    hypothesis: str = Field(min_length=10, max_length=1200)
    rationale: str = Field(min_length=10, max_length=1200)
    requests: tuple[AnalysisRequest, ...] = Field(max_length=3)


class DraftAnswer(Draft):
    question: CheckQuestion
    answer: str = Field(min_length=10, max_length=1200)


class BullMemoDraft(Draft):
    security_scope: tuple[str, ...] = Field(min_length=1, max_length=20)
    horizon: str = Field(min_length=3, max_length=120)
    hypothesis: str = Field(min_length=10, max_length=1200)
    economic_rationale: str = Field(min_length=10, max_length=1200)
    evidence_for: tuple[str, ...] = Field(max_length=12)
    evidence_against: tuple[str, ...] = Field(max_length=12)
    invalidation_conditions: tuple[str, ...] = Field(min_length=2, max_length=8)
    stance: Literal["LONG_CANDIDATE", "MORE_RESEARCH", "NO_TRADE"]
    entry: EntryArchetype
    exit: ExitArchetype
    raw_confidence: float = Field(ge=0, le=1)
    uncertainties: tuple[str, ...] = Field(min_length=1, max_length=12)
    answers: tuple[DraftAnswer, ...] = Field(min_length=7, max_length=7)
    no_trade_reason: str | None = Field(max_length=1200)

    @model_validator(mode="after")
    def complete_challenge(self) -> Self:
        if {item.question for item in self.answers} != set(CheckQuestion):
            raise ValueError("all seven self-falsification questions are required")
        if self.stance == "NO_TRADE" and not self.no_trade_reason:
            raise ValueError("NO_TRADE requires a reason")
        if self.stance == "LONG_CANDIDATE" and not self.evidence_for:
            raise ValueError("a long candidate requires supporting evidence")
        if any(len(item.strip()) < 10 for item in self.invalidation_conditions):
            raise ValueError("invalidation conditions must be explicit")
        return self


class ResearchScreen(Artifact):
    context_hash: str
    snapshot_hash: str
    source_result_hash: str
    # Deterministic trailing-feature rank; it is never an order or an alpha verdict.
    research_queue: tuple[str, ...]
    unranked: tuple[str, ...]
    note: str = "Queue for investigation only; feature rank is not a buy signal."


class ResearchTransition(Artifact):
    run_id: str
    context_hash: str
    sequence: int = Field(ge=0)
    state: AgentState
    task: str
    tool_result_hashes: tuple[str, ...] = ()


class EvidenceSection(Artifact):
    name: str
    result_hash: str
    status: EvidenceStatus
    note: str


class BullResearchMemo(AgentResearchMemo):
    preferred_exit_archetype: ExitArchetype
    screen_hash: str
    plan_hash: str
    evidence_sections: tuple[EvidenceSection, ...]
    self_falsification: tuple[DraftAnswer, ...]
    data_kind: str
    outcome_status: Literal["NOT_TESTED"] = "NOT_TESTED"
    note: str = "Unvalidated research, not an order. Raw confidence is an opinion."


class FrozenResearchPlan(Artifact):
    context_hash: str
    plan: ResearchPlan
