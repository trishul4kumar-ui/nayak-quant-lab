from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator

from quantlab.core.identifiers import InstrumentId
from quantlab.core.time import PointInTime


class AssetClass(StrEnum):
    EQUITY = "equity"
    FUTURE = "future"
    OPTION = "option"
    INDEX = "index"
    CASH = "cash"


class BarInterval(StrEnum):
    DAY = "1d"
    MINUTE = "1m"


class Side(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(StrEnum):
    CREATED = "created"
    VALIDATING = "validating"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLED = "cancelled"
    FAILED = "failed"
    UNKNOWN = "unknown"
    RECONCILING = "reconciling"
    RISK_PENDING = "risk_pending"


class RiskVerdict(StrEnum):
    APPROVE = "approve"
    MODIFY = "modify"
    REJECT = "reject"


class ExperimentStatus(StrEnum):
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"


class Instrument(BaseModel):
    id: InstrumentId
    lot_size: int = 1
    tick_size: float = 0.05
    currency: str = "INR"
    listed: bool = True
    name: str = ""
    listing_date: str | None = None
    delisting_date: str | None = None
    isin: str = ""
    security_id: str = ""

    @field_validator("lot_size")
    @classmethod
    def _lot(cls, value: int) -> int:
        if value < 1:
            raise ValueError("lot_size must be >= 1")
        return value


class OHLCVBar(BaseModel):
    instrument: InstrumentId
    pit: PointInTime
    interval: BarInterval = BarInterval.DAY
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    dataset_version: str = ""
    source_id: str = ""
    session_date: str = ""
    price_kind: str = "raw_price"
    data_kind: str = "synthetic"

    @model_validator(mode="after")
    def _ohlc(self) -> OHLCVBar:
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high must be the session high")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low must be the session low")
        if self.volume < 0:
            raise ValueError("volume cannot be negative")
        return self


class PriceState(BaseModel):
    close: float
    simple_return: float | None = None
    log_return: float | None = None


class VolatilityState(BaseModel):
    realized: float | None = None


class LiquidityState(BaseModel):
    volume: float = 0.0
    dollar_volume: float | None = None


class TrendState(BaseModel):
    momentum: float | None = None


class MarketState(BaseModel):
    """Canonical as-of market representation. Strategies should prefer this over raw bars."""

    instrument: InstrumentId
    as_of: datetime
    pit: PointInTime
    price: PriceState
    volatility: VolatilityState = Field(default_factory=VolatilityState)
    liquidity: LiquidityState = Field(default_factory=LiquidityState)
    trend: TrendState = Field(default_factory=TrendState)
    features: dict[str, float] = Field(default_factory=dict)


class Signal(BaseModel):
    instrument: InstrumentId
    score: float
    as_of: datetime


class TargetPosition(BaseModel):
    instrument: InstrumentId
    weight: float
    quantity: float | None = None


class ProposedPortfolio(BaseModel):
    as_of: datetime
    targets: list[TargetPosition]
    reason: str = ""

    @property
    def gross_exposure(self) -> float:
        return sum(abs(t.weight) for t in self.targets)

    @property
    def net_exposure(self) -> float:
        return sum(t.weight for t in self.targets)


class RiskDecision(BaseModel):
    verdict: RiskVerdict
    reasons: list[str] = Field(default_factory=list)
    modified: ProposedPortfolio | None = None


class Order(BaseModel):
    id: str
    instrument: InstrumentId
    side: Side
    quantity: float
    order_type: OrderType = OrderType.MARKET
    status: OrderStatus = OrderStatus.CREATED
    limit_price: float | None = None


class Fill(BaseModel):
    order_id: str
    instrument: InstrumentId
    quantity: float
    price: float
    pit: PointInTime


class Position(BaseModel):
    instrument: InstrumentId
    quantity: float
    avg_price: float = 0.0


class PortfolioState(BaseModel):
    cash: float
    positions: list[Position] = Field(default_factory=list)
    equity: float = 0.0


class StrategyContext(BaseModel):
    as_of: datetime
    bars: list[OHLCVBar] = Field(default_factory=list)
    market_states: list[MarketState] = Field(default_factory=list)


class ExperimentRun(BaseModel):
    id: str
    name: str
    hypothesis: str
    status: ExperimentStatus = ExperimentStatus.RUNNING
    git_commit: str | None = None
    dataset_version: str
    universe: list[str]
    feature_versions: dict[str, str] = Field(default_factory=dict)
    label_definition: str = ""
    hyperparameters: dict[str, float | int | str] = Field(default_factory=dict)
    training_period: str = ""
    validation_period: str = ""
    test_period: str = ""
    transaction_cost_bps: float = 0.0
    slippage_model: str = "none"
    random_seed: int = 0
    hypothesis_id: str = ""
    alpha_id: str = ""
    genome_id: str = ""
    cost_model: str = "proportional_bps"
    latency_model: str = "none"
    dataset_id: str = ""
    snapshot_id: str = ""
    universe_version: str = ""
    calendar_version: str = ""
    data_kind: str = "synthetic"
    price_adjustment_method: str = "raw_price"
    corporate_action_policy: str = "none"
    lineage: dict[str, str] = Field(default_factory=dict)
    metrics: dict[str, float] = Field(default_factory=dict)
    integrity: dict[str, str] = Field(default_factory=dict)
    application_version: str = ""
    conclusion: str = ""
    config_hash: str = ""
    research_family_id: str = ""
    parent_experiment_id: str = ""
    n_hypotheses_in_family: int = 1
    selection_stage: str = ""
    gate_outcome: str = ""
    gate_reasons: dict[str, str] = Field(default_factory=dict)
    validation_protocol: str = "next_bar_cost_adjusted"
    git_dirty: bool = False
    python_version: str = ""
    validation: dict[str, str] = Field(default_factory=dict)
    feature_id: str = ""
    feature_version: str = ""
    label_id: str = ""
    feature_identity_hash: str = ""
    portfolio_id: str = ""
    portfolio_version: str = ""
    ensemble_id: str = ""
    optimizer: str = ""
    risk_model_id: str = ""
    risk_model_version: str = ""
    factor_id: str = ""
    factor_set: str = ""
    factor_versions: dict[str, str] = Field(default_factory=dict)
    regime_model_id: str = ""
    regime_model_version: str = ""
    adaptive_model_id: str = ""
    adaptive_model_version: str = ""
    adaptation_policy: str = ""
    statistical_model_id: str = ""
    statistical_model_version: str = ""
    algorithm: str = ""
    combination_method: str = ""
    weighting_policy: str = ""
    meta_alpha_id: str = ""
    component_ids: str = ""
    candidate_count: int = 0
    strategy_id: str = ""
    execution_model_id: str = ""
    execution_model_version: str = ""
    scenario_id: str = ""
    scenario_version: str = ""
    research_type: str = ""
    search_space_id: str = ""
    tested_count: int = 0
    selection_policy: str = ""
    stopping_policy: str = ""
    multiple_testing_method: str = ""
    baseline_id: str = ""
    orchestration_id: str = ""
    hypothesis_version: str = ""
    discovery_run_id: str = ""
    expression_hash: str = ""
    generation: int = 0
    complexity_score: float = 0.0
    novelty_class: str = ""
    search_family_id: str = ""
    grammar_version: str = ""
    knowledge_snapshot_id: str = ""
    knowledge_graph_id: str = ""
    claim_id: str = ""
    decision_id: str = ""
    capital_policy_id: str = ""
    risk_budget_id: str = ""
    allocation_method: str = ""
    decision_status: str = ""
    abstention_code: str = ""
    capital_state: str = ""
    allocation_confidence: float = 0.0
    target_portfolio_hash: str = ""
    oms_run_id: str = ""
    order_plan_hash: str = ""
    paper_account_id: str = ""
    reconciliation_hash: str = ""
    decision_hash: str = ""
    monitoring_run_id: str = ""
    performance_snapshot_id: str = ""
    performance_hash: str = ""
    attribution_hash: str = ""
    observed_portfolio_hash: str = ""
    benchmark_id: str = ""
    attribution_method: str = ""
    residual_pnl: float = 0.0
    research_feedback_id: str = ""
    dataset_checksum: str = ""
    security_master_version: str = ""
    corporate_action_version: str = ""
    data_snapshot_hash: str = ""
    tca_run_id: str = ""
    tca_hash: str = ""
    calibration_hash: str = ""
    arrival_price_policy: str = ""
    shortfall: float = 0.0
    cost_decomposition: str = ""
    capacity_policy_id: str = ""
    capacity_result_id: str = ""
    fragility_status: str = ""
    econometrics_run_id: str = ""
    econometrics_hash: str = ""
    econometric_spec_id: str = ""
    certification_id: str = ""
    candidate_id: str = ""
    checklist_hash: str = ""
    validation_hash: str = ""
    certification_state: str = ""
    model_risk_severity: str = ""
    shadow_cycle_id: str = ""
    shadow_order_id: str = ""
    shadow_fill_id: str = ""
    shadow_mode: str = ""
    market_snapshot_hash: str = ""
    shadow_account_id: str = ""
    production_run: bool = False
    data_freshness_ms: float = 0.0
    decision_latency_ms: float = 0.0
    execution_latency_ms: float = 0.0
    authorization_id: str = ""
    safety_state: str = ""
    kill_switch_active: bool = False
    release_blocked: bool = True
    ops_run_id: str = ""
    ops_environment: str = ""
    ops_config_hash: str = ""
    backup_id: str = ""
    process_id: str = ""
    live_certification_id: str = ""
    live_certification_hash: str = ""
    release_id: str = ""
    release_manifest_hash: str = ""
    approval_id: str = ""
    broker_connection_id: str = ""
    adapter_id: str = ""
    account_snapshot_id: str = ""
    reconciliation_id: str = ""
    snapshot_hash: str = ""
    gateway_version: str = ""
    realtime_snapshot_id: str = ""
    realtime_snapshot_hash: str = ""
    strategy_release_id: str = ""
    strategy_release_hash: str = ""
    realtime_decision_id: str = ""
    realtime_decision_hash: str = ""
    twin_run_id: str = ""
    twin_state_hash: str = ""
    twin_replay_hash: str = ""
