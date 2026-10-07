"""Frozen contexts and assessments; no position mutation surface exists here."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self

from pydantic import AwareDatetime, Field, model_validator

from quantlab.agents.hashing import Artifact


class PositionMode(StrEnum):
    PAPER = "PAPER"
    SHADOW = "SHADOW"


class ReviewTrigger(StrEnum):
    SCHEDULED = "SCHEDULED"
    PRICE_THRESHOLD = "PRICE_THRESHOLD"
    STOP_PROXIMITY = "STOP_PROXIMITY"
    TARGET_PROXIMITY = "TARGET_PROXIMITY"
    REGIME_CHANGE = "REGIME_CHANGE"
    FACTOR_DETERIORATION = "FACTOR_DETERIORATION"
    VOLATILITY_SHOCK = "VOLATILITY_SHOCK"
    LIQUIDITY_DETERIORATION = "LIQUIDITY_DETERIORATION"
    ACCOUNT_CHANGE = "ACCOUNT_CHANGE"
    CORPORATE_ACTION = "CORPORATE_ACTION"
    MANUAL = "MANUAL"


class SuggestedStance(StrEnum):
    HOLD = "HOLD"
    REDUCE_CANDIDATE = "REDUCE_CANDIDATE"
    EXIT_CANDIDATE = "EXIT_CANDIDATE"
    ADD_CANDIDATE = "ADD_CANDIDATE"
    MORE_RESEARCH = "MORE_RESEARCH"
    EMERGENCY_RISK_ALERT = "EMERGENCY_RISK_ALERT"


class ExitRuleState(Artifact):
    rule: str = Field(min_length=1, max_length=120)
    triggered: bool
    evidence_refs: tuple[str, ...] = Field(min_length=1, max_length=12)


class PositionReviewContext(Artifact):
    position_id: str = Field(min_length=1, max_length=160)
    mode: PositionMode
    original_candidate_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    original_level_plan_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    original_exit_policy_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    original_thesis: str = Field(min_length=1, max_length=1_000)
    entry_fill_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    snapshot_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    current_price: float = Field(gt=0)
    entry_price: float = Field(gt=0)
    unrealized_pnl: float
    pnl_attribution: tuple[str, ...] = Field(min_length=1, max_length=12)
    factor_summary_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    regime: str = Field(min_length=1, max_length=120)
    volatility: float = Field(gt=0)
    liquidity_status: str = Field(min_length=1, max_length=80)
    portfolio_risk_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    position_opened_at: AwareDatetime
    trigger: ReviewTrigger
    exit_rules: tuple[ExitRuleState, ...] = Field(min_length=1, max_length=16)
    market_freshness: Literal["fresh", "stale", "unknown"]
    position_closed: bool = False

    @model_validator(mode="after")
    def bounded_context(self) -> Self:
        if self.created_at < self.position_opened_at:
            raise ValueError("review cannot predate position opening")
        if len({rule.rule for rule in self.exit_rules}) != len(self.exit_rules):
            raise ValueError("exit rule states must be unique")
        return self


class PositionView(Artifact):
    role: Literal["BULL", "BEAR"]
    context_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    thesis_status: Literal["INTACT", "WEAKENING", "INVALIDATED", "UNKNOWN"]
    evidence_refs: tuple[str, ...] = Field(min_length=1, max_length=16)
    confidence: float = Field(ge=0, le=1)
    commentary: str = Field(min_length=1, max_length=1_000)
    execution_authority: Literal[False] = False


class PositionAssessment(Artifact):
    position_id: str
    context_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    bull_view_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    bear_view_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    thesis_status: Literal["INTACT", "WEAKENING", "INVALIDATED", "UNKNOWN"]
    exit_rule_states: tuple[ExitRuleState, ...]
    suggested_stance: SuggestedStance
    evidence_refs: tuple[str, ...]
    confidence: float = Field(ge=0, le=1)
    hard_blockers: tuple[str, ...]
    execution_authority: Literal[False] = False


class PositionReviewSchedule(Artifact):
    """Persisted scheduler state; scheduling does not imply a model polling loop."""

    position_id: str = Field(min_length=1, max_length=160)
    next_review_at: AwareDatetime
    last_context_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    enabled: bool = True
    execution_authority: Literal[False] = False
