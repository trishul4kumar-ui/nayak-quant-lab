"""Capital-allocation domain types. Targets are not orders."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from quantlab.backtest.spec import config_hash
from quantlab.domain.research import CheckResult
from quantlab.portfolio.covariance import CovarianceReport
from quantlab.research.gate import ResearchGateResult


class DecisionStatus(StrEnum):
    REJECTED = "rejected"
    ABSTAIN = "abstain"
    RESEARCH_ONLY = "research_only"
    ELIGIBLE = "eligible"
    ALLOCATED = "allocated"
    PAPER_READY = "paper_ready"


class CapitalAllocationState(StrEnum):
    FULL = "full"
    REDUCED = "reduced"
    DEFENSIVE = "defensive"
    ABSTAIN = "abstain"
    HALT = "halt"


class DrawdownState(StrEnum):
    NORMAL = "normal"
    CAUTION = "caution"
    DEFENSIVE = "defensive"
    HALTED = "halted"


class SizingMethod(StrEnum):
    EQUAL_WEIGHT = "equal_weight"
    SCORE_WEIGHT = "score_weight"
    INVERSE_VOL = "inverse_vol"
    RISK_BUDGET = "risk_budget"
    VOL_TARGET = "vol_target"
    FRACTIONAL_KELLY = "fractional_kelly"
    CONFIDENCE_SCALED = "confidence_scaled"
    HYBRID = "hybrid"


class RiskBudgetMethod(StrEnum):
    EQUAL_RISK = "equal_risk"
    INVERSE_VOLATILITY = "inverse_volatility"
    RISK_PARITY = "risk_parity"
    FACTOR_RISK_BUDGET = "factor_risk_budget"
    HIERARCHICAL_RISK_BUDGET = "hierarchical_risk_budget"
    CUSTOM_BUDGET = "custom_budget"


class MarketMode(StrEnum):
    LONG_ONLY = "long_only"
    LONG_BIAS = "long_bias"
    DOLLAR_NEUTRAL = "dollar_neutral"
    BETA_NEUTRAL = "beta_neutral"
    FACTOR_NEUTRAL = "factor_neutral"
    LONG_SHORT = "long_short"


class ExpectedReturnSource(StrEnum):
    ALPHA = "alpha"
    ENSEMBLE = "ensemble"
    MODEL = "model"
    ADAPTIVE_MODEL = "adaptive_model"
    RESEARCH_OVERRIDE = "research_override"
    BASELINE = "baseline"


class LiquidityStatus(StrEnum):
    KNOWN = "known"
    UNKNOWN = "unknown"
    INSUFFICIENT = "insufficient"


class AbstentionCode(StrEnum):
    NONE = "none"
    GATE_FAIL = "gate_fail"
    PIT_INTEGRITY_FAIL = "pit_integrity_fail"
    RISK_UNAVAILABLE = "risk_unavailable"
    COVARIANCE_INVALID = "covariance_invalid"
    UNKNOWN_LIQUIDITY = "unknown_liquidity"
    UNKNOWN_FACTOR = "unknown_factor"
    EXPECTED_RETURN_UNAVAILABLE = "expected_return_unavailable"
    CONFIDENCE_BELOW_THRESHOLD = "confidence_below_threshold"
    DRAWDOWN_HALT = "drawdown_halt"
    CONSTRAINT_INFEASIBLE = "constraint_infeasible"
    EXECUTION_DRAG = "execution_drag"
    DATA_QUALITY = "data_quality"
    MODEL_STABILITY = "model_stability"
    KELLY_UNRELIABLE = "kelly_unreliable"
    TARGET_UNACHIEVABLE = "target_unachievable"
    CAPITAL_INSUFFICIENT = "capital_insufficient"
    LIVE_PATH_CLOSED = "live_path_closed"
    SYNTHETIC_RESEARCH_ONLY = "synthetic_research_only"


class VolTargetStatus(StrEnum):
    ACHIEVED = "achieved"
    TARGET_UNACHIEVABLE = "target_unachievable"
    NOT_TESTED = "not_tested"


class DrawdownLimits(BaseModel):
    model_config = ConfigDict(frozen=True)

    caution: float = 0.05
    defensive: float = 0.10
    halt: float = 0.15


class AllocationMultipliers(BaseModel):
    model_config = ConfigDict(frozen=True)

    full: float = 1.0
    reduced: float = 0.5
    defensive: float = 0.25
    abstain: float = 0.0
    halt: float = 0.0


class LiquidityPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    participation_limit: float = 0.10
    strict_unknown: bool = True
    abstain_on_insufficient: bool = True


class ConfidencePolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    threshold: float = 0.0
    reduce_below: float = 0.35
    abstain_below: float = 0.0


class ConstraintPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    hard_limits: bool = True
    fallback_sizing: str = ""
    abstain_on_infeasible: bool = False
    turnover_hard: bool = True
    strict_missing_covariance: bool = True
    strict_unknown_factor: bool = False
    allow_research_only_on_warn: bool = True
    require_gate: bool = False


class CapitalPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    policy_id: str
    version: str = "1"
    base_currency: str = "INR"
    starting_capital: float = 1_000_000.0
    available_capital: float = 1_000_000.0
    gross_leverage_limit: float = 1.0
    net_exposure_limit: float = 1.0
    cash_floor: float = 0.05
    max_position_weight: float = 0.40
    max_single_name_risk: float = 0.50
    max_turnover: float = 1.0
    target_volatility: float = 0.15
    volatility_lookback: int = 60
    risk_budget_method: RiskBudgetMethod = RiskBudgetMethod.EQUAL_RISK
    kelly_fraction: float = 0.25
    kelly_cap: float = 0.25
    sizing_method: SizingMethod = SizingMethod.HYBRID
    market_mode: MarketMode = MarketMode.LONG_ONLY
    max_top_5_weight: float = 1.0
    max_top_10_weight: float = 1.0
    max_hhi: float = 1.0
    min_beta: float | None = None
    max_beta: float | None = None
    max_factor_exposure: float | None = None
    min_factor_exposure: float | None = None
    min_trade_threshold: float = 0.0
    rebalance_band: float = 0.0
    drawdown_limits: DrawdownLimits = Field(default_factory=DrawdownLimits)
    allocation_multipliers: AllocationMultipliers = Field(default_factory=AllocationMultipliers)
    liquidity_policy: LiquidityPolicy = Field(default_factory=LiquidityPolicy)
    confidence_policy: ConfidencePolicy = Field(default_factory=ConfidencePolicy)
    constraint_policy: ConstraintPolicy = Field(default_factory=ConstraintPolicy)
    created_at: datetime = Field(default_factory=lambda: datetime(2024, 1, 15, tzinfo=UTC))
    config_hash: str = ""

    def with_hash(self) -> CapitalPolicy:
        payload = self.model_dump(mode="json", exclude={"config_hash", "created_at"})
        return self.model_copy(update={"config_hash": config_hash(payload)})


class CapitalBooks(BaseModel):
    """Explicit capital accounting. Never silently set capital = portfolio value."""

    equity: float
    cash: float
    reserved_cash: float = 0.0
    investable_capital: float = 0.0
    gross_exposure: float = 0.0
    net_exposure: float = 0.0
    margin_usage: float = 0.0
    available_margin: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    note: str = "research simulated books; not a live broker balance"


class ExpectedReturn(BaseModel):
    values: dict[str, float] = Field(default_factory=dict)
    source: ExpectedReturnSource = ExpectedReturnSource.BASELINE
    horizon: int = 1
    confidence: float = 0.5
    override_recorded: bool = False
    note: str = "Sharpe is not expected return"


class ConfidenceBundle(BaseModel):
    research_confidence: float = 0.5
    statistical_confidence: float = 0.5
    model_stability: float = 0.5
    execution_confidence: float = 0.5
    data_quality: float = 0.5
    evidence_strength: float = 0.5

    def allocation_confidence(self) -> float:
        parts = (
            self.research_confidence,
            self.statistical_confidence,
            self.model_stability,
            self.execution_confidence,
            self.data_quality,
            self.evidence_strength,
        )
        return max(0.0, min(1.0, sum(parts) / len(parts)))


class ConstraintCheck(BaseModel):
    name: str
    result: CheckResult
    bound: float | None = None
    value: float | None = None
    note: str = ""


class SizingResult(BaseModel):
    method_id: str
    parameters: dict[str, float | str] = Field(default_factory=dict)
    input_versions: dict[str, str] = Field(default_factory=dict)
    output_weights: dict[str, float] = Field(default_factory=dict)
    diagnostics: dict[str, str] = Field(default_factory=dict)


class AllocationRequest(BaseModel):
    policy_id: str = "CAP-RESEARCH-001"
    as_of: datetime = Field(default_factory=lambda: datetime(2024, 1, 15, tzinfo=UTC))
    snapshot_id: str = "seed"
    dataset_checksum: str = "seed"
    scores: dict[str, float] = Field(default_factory=dict)
    expected_return_source: ExpectedReturnSource = ExpectedReturnSource.BASELINE
    expected_return_horizon: int = 1
    expected_return_confidence: float = 0.5
    vols: dict[str, float] = Field(default_factory=dict)
    covariance: CovarianceReport | None = None
    previous_weights: dict[str, float] = Field(default_factory=dict)
    gate: ResearchGateResult | None = None
    data_kind: str = "synthetic"
    live_trading: bool = False
    factor_exposures: dict[str, float | None] = Field(default_factory=dict)
    liquidity_adv: dict[str, float | None] = Field(default_factory=dict)
    execution_cost: dict[str, float] = Field(default_factory=dict)
    drawdown: float = 0.0
    books: CapitalBooks | None = None
    portfolio_spec_id: str = "mom20_topn"
    experiment_id: str = ""
    research_result_id: str = ""
    knowledge_snapshot_id: str = "KS-SEED-001"
    strategy_id: str = "seed"
    ensemble_id: str = ""
    risk_policy_id: str = "seed"
    input_alpha_version: str = "seed"
    risk_model_version: str = "seed"
    covariance_version: str = "seed"
    regime_version: str = "seed"
    execution_model_version: str = "seed"
    confidence: ConfidenceBundle = Field(default_factory=ConfidenceBundle)
    risk_budget: dict[str, float] = Field(default_factory=dict)
    n_obs_returns: int = 0
    future_payload_ignored: dict[str, str] = Field(default_factory=dict)


class TargetPortfolio(BaseModel):
    model_config = ConfigDict(frozen=True)

    portfolio_id: str
    decision_id: str
    timestamp: datetime
    weights: dict[str, float] = Field(default_factory=dict)
    notional_targets: dict[str, float] = Field(default_factory=dict)
    gross_exposure: float = 0.0
    net_exposure: float = 0.0
    cash_target: float = 0.0
    risk_target: float | None = None
    turnover_estimate: float = 0.0
    constraint_state: list[ConstraintCheck] = Field(default_factory=list)
    portfolio_hash: str = ""
    note: str = "Target portfolio only. Prompt 17 does not construct orders."


class InvestmentDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    decision_id: str
    decision_time: datetime
    snapshot_id: str
    experiment_id: str = ""
    research_result_id: str = ""
    knowledge_snapshot_id: str = ""
    strategy_id: str = ""
    ensemble_id: str = ""
    portfolio_spec_id: str = ""
    risk_policy_id: str = ""
    capital_policy_id: str = ""
    decision_status: DecisionStatus
    input_alpha_version: str = ""
    risk_model_version: str = ""
    covariance_version: str = ""
    regime_version: str = ""
    execution_model_version: str = ""
    expected_return: dict[str, float] = Field(default_factory=dict)
    expected_return_source: str = ""
    expected_risk: float | None = None
    expected_volatility: float | None = None
    gross_target: float = 0.0
    net_target: float = 0.0
    target_weights: dict[str, float] = Field(default_factory=dict)
    risk_contribution: dict[str, float] = Field(default_factory=dict)
    factor_exposure: float | None = None
    factor_exposure_status: CheckResult = CheckResult.NOT_TESTED
    constraint_status: list[ConstraintCheck] = Field(default_factory=list)
    turnover_estimate: float = 0.0
    liquidity_status: LiquidityStatus = LiquidityStatus.UNKNOWN
    confidence: float = 0.0
    evidence_status: str = ""
    abstention_code: AbstentionCode = AbstentionCode.NONE
    abstention_reason: str = ""
    abstention_stage: str = ""
    capital_state: CapitalAllocationState = CapitalAllocationState.FULL
    drawdown_state: DrawdownState = DrawdownState.NORMAL
    allocation_method: str = ""
    data_kind: str = "synthetic"
    warnings: list[str] = Field(default_factory=list)
    stages: list[str] = Field(default_factory=list)
    config_hash: str = ""
    decision_hash: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime(2024, 1, 15, tzinfo=UTC))
    software_version: str = ""
    live_trading: bool = False
    note: str = "Immutable investment decision. Not an order."
