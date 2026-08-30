"""Learner and efficacy state. Descriptive; not permission to trade."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from quantlab.domain.research import CheckResult


class DriftStatus(StrEnum):
    STABLE = "stable"
    WATCH = "watch"
    DRIFT_DETECTED = "drift_detected"
    INSUFFICIENT_DATA = "insufficient_data"
    UNAVAILABLE = "unavailable"


class DecayStatus(StrEnum):
    ESTIMABLE = "estimable"
    INSUFFICIENT_DATA = "insufficient_data"
    UNSTABLE = "unstable"
    NOT_TESTED = "not_tested"


class OnlineObservation(BaseModel):
    as_of: datetime
    available_at: datetime
    ic: float | None = None
    regime: str | None = None
    note: str = "outcome available_at must be <= the next decision time"


class UpdateEvent(BaseModel):
    decision_time: datetime
    outcome_as_of: datetime
    n_updates: int
    efficacy: float | None = None
    note: str = "update after scoring the frozen prediction"


class ResetEvent(BaseModel):
    reset_time: datetime
    reason: str
    trigger_metric: float | None = None
    threshold: float | None = None
    old_n_updates: int
    new_n_updates: int = 0


class AdaptiveModelState(BaseModel):
    schema_version: str = "1"
    as_of: datetime
    model_id: str
    n_updates: int = 0
    ic_history: list[float] = Field(default_factory=list)
    ic_times: list[datetime] = Field(default_factory=list)
    weights: dict[str, float] = Field(default_factory=dict)
    efficacy: float | None = None
    posterior_a: float = 1.0
    posterior_b: float = 1.0
    ess: float | None = None
    drift_status: DriftStatus = DriftStatus.INSUFFICIENT_DATA
    last_reset: datetime | None = None
    status: CheckResult = CheckResult.NOT_TESTED
    note: str = ""


class AlphaEfficacyState(BaseModel):
    alpha_id: str
    as_of: datetime
    rolling_ic: float | None = None
    sample_size: int = 0
    estimated_decay: float | None = None
    regime: str | None = None
    drift_status: DriftStatus = DriftStatus.INSUFFICIENT_DATA
    confidence: float | None = None
    note: str = "Descriptive research state. Not a trading permission."


class DecayEstimate(BaseModel):
    method: str
    estimate: float | None = None
    confidence_interval: tuple[float, float] | None = None
    sample_size: int = 0
    fit_quality: float | None = None
    status: DecayStatus = DecayStatus.NOT_TESTED
    warnings: list[str] = Field(default_factory=list)
    note: str = "Do not manufacture a half-life when the series cannot support one"


class StabilityReport(BaseModel):
    schema_version: str = "1"
    n_sign_changes: int = 0
    weight_hhi: float | None = None
    oscillation_rate: float | None = None
    flags: list[str] = Field(default_factory=list)
    status: CheckResult = CheckResult.PASS
    note: str = "Stability of adaptation, not of markets"
