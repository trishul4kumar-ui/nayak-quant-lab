"""Frozen monitoring domain types. Performance is not a claim and not alpha."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from quantlab.domain.research import CheckResult
from quantlab.monitoring.enums import (
    AttributionMethod,
    BenchmarkKind,
    DriftStatus,
    FeedbackKind,
    MonitoringRunStatus,
    ReturnKind,
)


class EquityPoint(BaseModel):
    model_config = ConfigDict(frozen=True)

    as_of: datetime
    cash: float
    reserved_cash: float = 0.0
    market_value: float
    equity: float
    note: str = ""


class PnLBreakdown(BaseModel):
    model_config = ConfigDict(frozen=True)

    beginning_equity: float
    ending_equity: float
    cash: float
    reserved_cash: float = 0.0
    gross_exposure: float = 0.0
    net_exposure: float = 0.0
    long_exposure: float = 0.0
    short_exposure: float | None = None
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    income: float | None = None
    costs: float | None = None
    fees: float | None = None
    financing: float | None = None
    adjustments: float | None = None
    residual_pnl: float = 0.0
    pnl_total: float = 0.0
    net_return: float | None = None
    identity_ok: bool = True
    note: str = "Unknown legs remain None / NOT_TESTED, never silently zero."


class SecurityContribution(BaseModel):
    model_config = ConfigDict(frozen=True)

    security_id: str
    pnl: float
    return_contribution: float
    realized: float = 0.0
    unrealized: float = 0.0
    cost: float = 0.0
    turnover: float = 0.0
    drawdown_share: float | None = None
    exposure_share: float = 0.0


class AttributionResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    method: AttributionMethod
    total: float
    residual: float
    contributions: list[SecurityContribution] = Field(default_factory=list)
    factor_contributions: dict[str, float] | None = None
    alpha_contributions: dict[str, float] | None = None
    status: CheckResult = CheckResult.NOT_TESTED
    note: str = ""


class DriftObservation(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: DriftStatus
    weight_drift: dict[str, float] = Field(default_factory=dict)
    quantity_drift: dict[str, float] = Field(default_factory=dict)
    cash_drift: float = 0.0
    exposure_drift: float = 0.0
    implementation_gap: float = 0.0
    unfilled_quantity: dict[str, float] = Field(default_factory=dict)
    residual_orders: int = 0
    note: str = "Drift is observed. The monitor does not rebalance."


class DrawdownEpisode(BaseModel):
    model_config = ConfigDict(frozen=True)

    peak_equity: float
    trough_equity: float
    drawdown: float
    start: datetime
    trough: datetime
    recovered: datetime | None = None
    duration_sessions: int | None = None


class RiskObservation(BaseModel):
    model_config = ConfigDict(frozen=True)

    current_drawdown: float = 0.0
    max_drawdown: float = 0.0
    rolling_volatility: float | None = None
    concentration: float = 0.0
    gross_exposure: float = 0.0
    net_exposure: float = 0.0
    turnover: float = 0.0
    episodes: list[DrawdownEpisode] = Field(default_factory=list)
    note: str = "Monitoring does not change risk limits."


class ResearchFeedback(BaseModel):
    model_config = ConfigDict(frozen=True)

    feedback_id: str
    kind: FeedbackKind
    observation: str
    attribution: str
    interpretation: str
    research_question: str
    is_hypothesis: bool = False
    note: str = "Feedback is not automatically a new hypothesis."


class BenchmarkSeries(BaseModel):
    model_config = ConfigDict(frozen=True)

    benchmark_id: str
    kind: BenchmarkKind
    returns: list[float] = Field(default_factory=list)
    relative_return: float | None = None
    status: CheckResult = CheckResult.NOT_TESTED
    note: str = "NIFTY is NOT_TESTED until a sourced PIT series exists."


class ReturnReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: ReturnKind
    value: float | None
    status: CheckResult
    annualized: float | None = None
    note: str = ""


class PerformanceSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    snapshot_id: str
    as_of: datetime
    equity: EquityPoint
    pnl: PnLBreakdown
    snapshot_hash: str = ""
    note: str = "Synthetic diagnostic snapshot unless data_kind=real."


class MonitoringRun(BaseModel):
    model_config = ConfigDict(frozen=True)

    monitoring_run_id: str
    decision_hash: str
    oms_run_id: str
    snapshot_id: str
    methodology_id: str
    as_of: datetime
    status: MonitoringRunStatus
    performance_hash: str = ""
    attribution_hash: str = ""
    run_hash: str = ""
    live_trading: bool = False
    note: str = "Monitoring run. Not a second backtest. Not a live book."


class MonitoringRequest(BaseModel):
    oms_run_id: str = "last"
    methodology_id: str = "accounting-v1"
    risk_free_rate: float = 0.0
    live_trading: bool = False
    data_kind: str = "synthetic"
    as_of: datetime = Field(default_factory=lambda: datetime(2024, 1, 15, tzinfo=UTC))
    future_payload_ignored: dict[str, str] = Field(default_factory=dict)
    user_benchmark_returns: list[float] | None = None
    factor_returns: dict[str, float] | None = None
    factor_exposures: dict[str, float] | None = None
    alpha_lineage: dict[str, float] | None = None


class MonitoringResult(BaseModel):
    run: MonitoringRun
    snapshot: PerformanceSnapshot
    pnl: PnLBreakdown
    returns: list[ReturnReport] = Field(default_factory=list)
    attribution: AttributionResult
    factor_attribution: AttributionResult
    alpha_attribution: AttributionResult
    drift: DriftObservation
    exposure: dict[str, float] = Field(default_factory=dict)
    concentration: float = 0.0
    turnover: float = 0.0
    drawdown: RiskObservation
    benchmark: BenchmarkSeries
    feedback: list[ResearchFeedback] = Field(default_factory=list)
    reconciliation_ok: bool = True
    live_trading: bool = False
    note: str = (
        "A profitable observation is not automatically alpha. "
        "The portfolio may have made money without establishing why."
    )
