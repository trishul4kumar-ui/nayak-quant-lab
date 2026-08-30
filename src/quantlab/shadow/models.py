"""Shadow domain types. Distinct from paper OMS and broker orders."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from quantlab.domain.models import Side
from quantlab.domain.research import IntegrityReport
from quantlab.paper_oms.models import PaperAccount, PaperOMSResult
from quantlab.shadow.enums import (
    CycleStatus,
    IncidentKind,
    IncidentSeverity,
    KillReason,
    PositionBook,
    ReplayOutcome,
    ResultKind,
    Score,
    SessionState,
    ShadowMode,
    ShadowOrderStatus,
    TriggerKind,
)


class ShadowConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    mode: ShadowMode = ShadowMode.RESEARCH_PAPER
    cycle_frequency: str = "manual"
    market: str = "NSE:CM"
    data_source: str = "synthetic_seed"
    max_data_age_ms: int = 300_000
    max_clock_skew_ms: int = 5_000
    max_processing_latency_ms: int = 60_000
    max_missing_interval: int = 1
    risk_policy: str = "research"
    capital_policy: str = "CAP-RESEARCH-001"
    execution_policy: str = "base"
    slippage_policy: str = "paper_oms"
    latency_policy: str = "recorded"
    certification_id: str = ""
    strategy_version: str = "seed-v1"
    model_versions: dict[str, str] = Field(default_factory=dict)
    configuration_hash: str = ""
    note: str = "Immutable shadow configuration. Not live routing."


class FreshnessRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    data_timestamp: datetime
    received_timestamp: datetime
    available_time: datetime
    decision_time: datetime
    processing_time: datetime
    latency_ms: float = 0.0
    age_ms: float = 0.0
    stale: bool = False
    calendar_status: str = "not_tested"
    note: str = ""


class DecisionTrigger(BaseModel):
    model_config = ConfigDict(frozen=True)

    trigger_id: str
    trigger_time: datetime
    source: TriggerKind = TriggerKind.MANUAL_PAPER_RUN
    decision_time: datetime


class FrozenSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    snapshot_id: str
    snapshot_hash: str
    market_data_hash: str
    feature_snapshot_hash: str = ""
    factor_state_hash: str = ""
    regime_state_hash: str = ""
    model_state_hash: str = ""
    adaptive_state_hash: str = ""
    ensemble_state_hash: str = ""
    risk_state_hash: str = ""
    capital_policy_hash: str = ""
    portfolio_state_hash: str = ""
    execution_policy_hash: str = ""
    configuration_hash: str = ""
    as_of: datetime
    note: str = "Frozen shadow snapshot. Immutable after freeze."


class ShadowIntent(BaseModel):
    model_config = ConfigDict(frozen=True)

    intent_id: str
    cycle_id: str
    security_id: str
    side: Side
    target_qty: float
    current_qty: float
    delta_qty: float
    reference_price: float
    notional: float
    reason: str
    decision_hash: str
    target_hash: str
    timestamp: datetime
    paper_intent_id: str = ""
    note: str = "Shadow order intent from Δq. Not a broker ticket."


class ShadowOrder(BaseModel):
    model_config = ConfigDict(frozen=True)

    shadow_order_id: str
    intent_id: str
    cycle_id: str
    security_id: str
    side: Side
    quantity: float
    filled_quantity: float = 0.0
    remaining_quantity: float = 0.0
    residual_quantity: float = 0.0
    reference_price: float
    arrival_time: datetime
    expected_fill_model: str = "paper_oms"
    execution_policy: str = "base"
    status: ShadowOrderStatus = ShadowOrderStatus.CREATED
    paper_order_id: str = ""
    routable: bool = False
    note: str = "Shadow order. Not routable. Not a broker working order."


class ShadowFill(BaseModel):
    model_config = ConfigDict(frozen=True)

    shadow_fill_id: str
    shadow_order_id: str
    cycle_id: str
    security_id: str
    side: Side
    reference_price: float
    execution_price: float
    spread_cost: float = 0.0
    slippage_cost: float = 0.0
    impact_cost: float = 0.0
    commission: float = 0.0
    other_cost: float = 0.0
    gross_notional: float = 0.0
    net_notional: float = 0.0
    filled_quantity: float
    residual_quantity: float
    fill_time: datetime
    paper_fill_id: str = ""
    broker_confirmed: bool = False
    note: str = "Simulated shadow fill. Not broker-confirmed."


class ShadowPosition(BaseModel):
    model_config = ConfigDict(frozen=True)

    security_id: str
    quantity: float
    market_price: float
    market_value: float
    book: PositionBook = PositionBook.SHADOW_POSITION
    note: str = "SHADOW_POSITION. Not PAPER_POSITION. Not BROKER_POSITION."


class ShadowPortfolio(BaseModel):
    model_config = ConfigDict(frozen=True)

    account_id: str
    book: PositionBook = PositionBook.SHADOW_POSITION
    cash: float
    market_value: float
    equity: float
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    fees: float = 0.0
    turnover: float = 0.0
    positions: dict[str, ShadowPosition] = Field(default_factory=dict)
    note: str = "Hypothetical shadow holdings. Not a brokerage account."


class LatencyRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    market_to_decision_ms: float = 0.0
    decision_to_intent_ms: float = 0.0
    intent_to_order_ms: float = 0.0
    order_to_fill_ms: float = 0.0
    total_cycle_ms: float = 0.0
    note: str = "Recorded shadow latencies. Not live exchange timestamps."


class ShadowReconciliation(BaseModel):
    model_config = ConfigDict(frozen=True)

    report_id: str
    reconciliation_hash: str = ""
    status: str
    paper_status: str = ""
    cash_difference: float = 0.0
    unexplained: dict[str, str] = Field(default_factory=dict)
    breaks: list[str] = Field(default_factory=list)
    note: str = "Shadow reconciliation. Breaks are retained."


class ShadowCompare(BaseModel):
    model_config = ConfigDict(frozen=True)

    decision_agreement: bool = True
    target_weight_difference: float = 0.0
    order_difference: float = 0.0
    fill_difference: float = 0.0
    slippage_difference: float = 0.0
    turnover_difference: float = 0.0
    pnl_difference: float = 0.0
    drawdown_difference: float = 0.0
    exposure_difference: float = 0.0
    reconciliation_difference: float = 0.0
    latency_difference: float = 0.0
    note: str = (
        "Diagnostic compare of labelled paper vs shadow books. "
        "Not a promotion gate. Not broker-equal."
    )


class ShadowIncident(BaseModel):
    model_config = ConfigDict(frozen=True)

    incident_id: str
    timestamp: datetime
    severity: IncidentSeverity
    source: str
    kind: IncidentKind
    description: str
    state: str = "open"
    resolution: str = ""
    lineage: dict[str, str] = Field(default_factory=dict)


class ShadowCheckpoint(BaseModel):
    model_config = ConfigDict(frozen=True)

    checkpoint_id: str
    cycle_id: str
    payload_hash: str
    portfolio_hash: str
    paper_account_id: str
    last_market_timestamp: datetime
    created_at: datetime
    note: str = "Shadow checkpoint. Corrupt files fail closed."


class ShadowCycle(BaseModel):
    model_config = ConfigDict(frozen=True)

    cycle_id: str
    run_id: str
    decision_time: datetime
    market_time: datetime
    data_snapshot_id: str
    data_snapshot_hash: str
    strategy_version: str
    feature_snapshot_hash: str = ""
    model_snapshot_hash: str = ""
    ensemble_snapshot_hash: str = ""
    regime_snapshot_hash: str = ""
    risk_snapshot_hash: str = ""
    capital_decision_hash: str = ""
    target_portfolio_hash: str = ""
    order_plan_hash: str = ""
    execution_policy_hash: str = ""
    configuration_hash: str = ""
    mode: ShadowMode
    requested_mode: ShadowMode
    status: CycleStatus
    created_at: datetime
    completed_at: datetime | None = None
    production_run: bool = False
    live_trading: bool = False
    note: str = "Immutable shadow cycle. Not a broker session."


class ReadinessScorecard(BaseModel):
    model_config = ConfigDict(frozen=True)

    data: Score = Score.NOT_TESTED
    pit: Score = Score.NOT_TESTED
    model: Score = Score.NOT_TESTED
    risk: Score = Score.NOT_TESTED
    capital: Score = Score.NOT_TESTED
    execution: Score = Score.NOT_TESTED
    reconciliation: Score = Score.NOT_TESTED
    monitoring: Score = Score.NOT_TESTED
    tca: Score = Score.NOT_TESTED
    certification: Score = Score.NOT_TESTED
    safety: Score = Score.NOT_TESTED
    recovery: Score = Score.NOT_TESTED
    observability: Score = Score.NOT_TESTED
    note: str = "Diagnostic scorecard. Not a single ready boolean. Not live."


class Heartbeat(BaseModel):
    model_config = ConfigDict(frozen=True)

    last_cycle: str = ""
    last_success: str = ""
    last_data: str = ""
    last_reconciliation: str = ""
    last_checkpoint: str = ""
    last_health_check: str = ""
    idle: bool = True
    dead: bool = False


class ShadowRequest(BaseModel):
    mode: ShadowMode = ShadowMode.RESEARCH_PAPER
    trigger: TriggerKind = TriggerKind.MANUAL_PAPER_RUN
    decision_time: datetime | None = None
    available_time: datetime | None = None
    data_timestamp: datetime | None = None
    received_timestamp: datetime | None = None
    session_override: SessionState | None = None
    live_trading: bool = False
    route_live: bool = False
    ai_override: bool = False
    require_certified: bool = False
    skip_reconciliation: bool = False
    recover: bool = False
    data_kind: str = "synthetic"
    strategy_version: str = "seed-v1"
    execution_policy_id: str = "base"
    account_id: str = ""
    max_data_age_ms: int | None = None
    future_payload_ignored: dict[str, str] = Field(default_factory=dict)


class ShadowResult(BaseModel):
    cycle: ShadowCycle
    config: ShadowConfig
    freshness: FreshnessRecord
    session: SessionState
    snapshot: FrozenSnapshot
    intents: list[ShadowIntent] = Field(default_factory=list)
    orders: list[ShadowOrder] = Field(default_factory=list)
    fills: list[ShadowFill] = Field(default_factory=list)
    portfolio: ShadowPortfolio
    paper_account: PaperAccount
    paper: PaperOMSResult | None = None
    reconciliation: ShadowReconciliation
    compare: ShadowCompare
    latency: LatencyRecord
    incidents: list[ShadowIncident] = Field(default_factory=list)
    checkpoint: ShadowCheckpoint | None = None
    scorecard: ReadinessScorecard
    heartbeat: Heartbeat
    integrity: IntegrityReport
    kill_reason: KillReason | None = None
    result_kind: ResultKind = ResultKind.RESEARCH_RESULT
    replay: ReplayOutcome | None = None
    live_trading: bool = False
    shadow_mode: bool = True
    broker_routing_enabled: bool = False
    live_order_submission_enabled: bool = False
    extras: dict[str, Any] = Field(default_factory=dict)
    note: str = (
        "Shadow result. Paper profit is not validated alpha. "
        "Shadow execution is not broker execution. LIVE_TRADING=false."
    )
