"""Immutable realized outcomes and released scorecards."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import AwareDatetime, Field, model_validator

from quantlab.agents.hashing import Artifact


class OutcomeStance(StrEnum):
    LONG = "LONG"
    BEARISH = "BEARISH"
    NO_TRADE = "NO_TRADE"


class ScoreStatus(StrEnum):
    RELEASED = "RELEASED"
    NOT_TESTED = "NOT_TESTED"


class RealizedOutcome(Artifact):
    outcome_id: str = Field(min_length=1, max_length=160)
    agent_id: str = Field(min_length=1, max_length=160)
    agent_version: str = Field(min_length=1, max_length=160)
    memo_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    candidate_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    level_plan_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    position_review_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    prediction_time: AwareDatetime
    realized_at: AwareDatetime
    stance: OutcomeStance
    raw_confidence: float = Field(ge=0, le=1)
    realized_return: float | None = None
    realized_volatility: float | None = Field(default=None, ge=0)
    realized_cost_bps: float | None = Field(default=None, ge=0)
    risk_event: bool | None = None
    regime: str = Field(min_length=1, max_length=120)
    paper_or_shadow: bool
    no_trade_counterfactual: bool = False

    @model_validator(mode="after")
    def temporal_integrity(self) -> Self:
        if self.realized_at < self.prediction_time:
            raise ValueError("realized outcome cannot predate the prediction")
        if self.created_at < self.realized_at:
            raise ValueError("outcome cannot be frozen before it is realized")
        if self.stance is OutcomeStance.NO_TRADE and not self.no_trade_counterfactual:
            raise ValueError("no-trade outcome needs an explicit counterfactual label")
        return self


class CalibrationPolicy(Artifact):
    policy_id: str
    minimum_sample_size: int = Field(ge=20, le=10_000)
    bin_count: int = Field(ge=2, le=20)


class ReliabilityBin(Artifact):
    lower: float = Field(ge=0, le=1)
    upper: float = Field(ge=0, le=1)
    sample_size: int = Field(ge=0)
    mean_raw_confidence: float | None = Field(default=None, ge=0, le=1)
    realized_hit_rate: float | None = Field(default=None, ge=0, le=1)


class AgentScorecard(Artifact):
    agent_id: str
    agent_version: str
    window_start: AwareDatetime
    window_end: AwareDatetime
    status: ScoreStatus
    sample_size: int = Field(ge=0)
    coverage: float = Field(ge=0, le=1)
    brier_score: float | None = Field(default=None, ge=0)
    hit_rate: float | None = Field(default=None, ge=0, le=1)
    calibrated_confidence: float | None = Field(default=None, ge=0, le=1)
    reliability: tuple[ReliabilityBin, ...]
    regime_sample_sizes: tuple[tuple[str, int], ...]
    warnings: tuple[str, ...]
    self_modifying: bool = False

    @model_validator(mode="after")
    def immutable_calibration_boundary(self) -> Self:
        if self.self_modifying:
            raise ValueError("runtime self-modification is forbidden")
        if self.status is ScoreStatus.NOT_TESTED and self.calibrated_confidence is not None:
            raise ValueError("small sample scorecards cannot publish calibrated confidence")
        return self
