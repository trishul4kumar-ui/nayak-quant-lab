"""Paper OMS domain types. Distinct from execution-research OrderIntent and domain.Order."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from quantlab.domain.models import Side
from quantlab.domain.research import CheckResult
from quantlab.paper_oms.enums import (
    EventType,
    FillPolicy,
    LiquidityMark,
    OMSRunStatus,
    OrderAction,
    OrderLifecycleState,
    PaperOrderType,
    ReconciliationStatus,
    RemainderFate,
    RoundingPolicy,
    TimeInForce,
)


class PaperMarketSnapshot(BaseModel):
    """PIT prices and optional volume at as_of. Missing volume is not infinite liquidity."""

    model_config = ConfigDict(frozen=True)

    snapshot_id: str
    as_of: datetime
    prices: dict[str, float] = Field(default_factory=dict)
    volumes: dict[str, float | None] = Field(default_factory=dict)
    tradable: dict[str, bool] = Field(default_factory=dict)
    lot_size: dict[str, int] = Field(default_factory=dict)
    note: str = "Synthetic research snapshot. Not NSE quotes."


class PaperPosition(BaseModel):
    model_config = ConfigDict(frozen=True)

    security_id: str
    quantity: float = 0.0
    average_cost: float = 0.0
    market_price: float = 0.0
    market_value: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    gross_exposure: float = 0.0
    weight: float = 0.0
    last_update: datetime = Field(default_factory=lambda: datetime(2024, 1, 15, tzinfo=UTC))

    def side_label(self) -> str:
        if abs(self.quantity) <= 1e-12:
            return "flat"
        if self.quantity > 0:
            return "long"
        return "short"


class CashLedger(BaseModel):
    model_config = ConfigDict(frozen=True)

    opening_cash: float
    deposits: float = 0.0
    purchases: float = 0.0
    sales: float = 0.0
    fees: float = 0.0
    closing_cash: float = 0.0


class PaperAccount(BaseModel):
    """Explicit paper books. Never define capital as portfolio market value alone."""

    model_config = ConfigDict(frozen=True)

    account_id: str
    cash: float
    reserved_cash: float = 0.0
    available_cash: float = 0.0
    positions: dict[str, PaperPosition] = Field(default_factory=dict)
    gross_exposure: float = 0.0
    net_exposure: float = 0.0
    market_value: float = 0.0
    equity: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    fees: float = 0.0
    slippage: float = 0.0
    impact: float = 0.0
    turnover: float = 0.0
    ledger: CashLedger | None = None
    allow_short: bool = False
    note: str = "Paper account. Not a live broker balance."


class OrderIntent(BaseModel):
    """Desired change implied by an approved target. Not an execution-research intent."""

    model_config = ConfigDict(frozen=True)

    intent_id: str
    intent_hash: str = ""
    decision_id: str
    decision_hash: str
    target_portfolio_id: str
    target_portfolio_hash: str
    capital_policy_id: str
    experiment_id: str = ""
    snapshot_id: str
    as_of: datetime
    security_id: str
    side: Side
    action: OrderAction
    target_weight: float
    current_weight: float
    weight_delta: float
    target_quantity: float
    current_quantity: float
    delta_quantity: float
    estimated_notional: float
    requested_quantity: float
    rounded_quantity: float
    residual_quantity: float
    residual_notional: float
    rounding_policy: RoundingPolicy = RoundingPolicy.FLOOR_LOT
    reference_price: float
    note: str = "Paper order intent. Not sent to a broker."


class PlannedInstruction(BaseModel):
    model_config = ConfigDict(frozen=True)

    security_id: str
    side: Side
    action: OrderAction
    quantity: float
    requested_quantity: float
    rounded_quantity: float
    residual_quantity: float
    residual_notional: float
    rounding_policy: RoundingPolicy
    order_type: PaperOrderType = PaperOrderType.MARKET
    limit_price: float | None = None
    reference_price: float
    time_in_force: TimeInForce = TimeInForce.DAY
    expected_arrival: datetime
    expected_fill_policy: FillPolicy = FillPolicy.SIMULATED
    intent_id: str
    intent_hash: str


class OrderPlan(BaseModel):
    model_config = ConfigDict(frozen=True)

    order_plan_id: str
    order_plan_hash: str = ""
    decision_hash: str
    intent_hash: str
    snapshot_id: str
    planning_time: datetime
    execution_policy_id: str
    instructions: list[PlannedInstruction] = Field(default_factory=list)
    residuals: dict[str, float] = Field(default_factory=dict)
    note: str = "Deterministic paper plan. Not a live ticket."


class PaperOrder(BaseModel):
    model_config = ConfigDict(frozen=True)

    order_id: str
    order_hash: str = ""
    idempotency_key: str
    plan_id: str
    plan_hash: str
    intent_id: str
    intent_hash: str
    decision_hash: str
    account_id: str
    security_id: str
    side: Side
    action: OrderAction
    order_type: PaperOrderType
    limit_price: float | None = None
    time_in_force: TimeInForce
    requested_quantity: float
    rounded_quantity: float
    residual_quantity: float
    filled_quantity: float = 0.0
    remaining_quantity: float = 0.0
    cancelled_quantity: float = 0.0
    expired_quantity: float = 0.0
    remainder_fate: RemainderFate = RemainderFate.OPEN
    reference_price: float
    state: OrderLifecycleState = OrderLifecycleState.CREATED
    rejection_reason: str = ""
    created_at: datetime
    arrival_time: datetime
    fill_time: datetime | None = None
    note: str = "Paper order. Not a broker working order."


class PaperFill(BaseModel):
    model_config = ConfigDict(frozen=True)

    fill_id: str
    fill_hash: str = ""
    order_id: str
    security_id: str
    side: Side
    requested_quantity: float
    filled_quantity: float
    remaining_quantity: float
    reference_price: float
    arrival_price: float
    execution_price: float
    gross_notional: float
    commission: float = 0.0
    taxes: float = 0.0
    fees: float = 0.0
    spread_cost: float = 0.0
    slippage_cost: float = 0.0
    impact_cost: float = 0.0
    total_cost: float = 0.0
    arrival_time: datetime
    fill_time: datetime
    latency_sessions: int = 0
    liquidity_status: LiquidityMark = LiquidityMark.NOT_TESTED
    execution_model_id: str
    note: str = "Simulated paper fill. Not broker-confirmed. Not a live execution."


class OrderEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: str
    order_id: str
    event_type: EventType
    event_time: datetime
    sequence_number: int
    previous_state: OrderLifecycleState | None
    new_state: OrderLifecycleState
    payload_hash: str
    causation_id: str = ""
    correlation_id: str = ""
    note: str = ""


class TargetPositionGap(BaseModel):
    model_config = ConfigDict(frozen=True)

    security_id: str
    target_weight: float
    actual_weight: float
    weight_error: float
    target_quantity: float
    actual_quantity: float
    quantity_error: float
    notional_error: float


class ReconciliationReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    report_id: str
    reconciliation_hash: str = ""
    status: ReconciliationStatus
    target_difference: dict[str, float] = Field(default_factory=dict)
    order_difference: dict[str, float] = Field(default_factory=dict)
    fill_difference: dict[str, float] = Field(default_factory=dict)
    position_difference: dict[str, float] = Field(default_factory=dict)
    cash_difference: float = 0.0
    unexplained_difference: dict[str, str] = Field(default_factory=dict)
    breaks: list[str] = Field(default_factory=list)
    gaps: list[TargetPositionGap] = Field(default_factory=list)
    note: str = "Paper reconciliation. Breaks are retained."


class OMSRun(BaseModel):
    model_config = ConfigDict(frozen=True)

    oms_run_id: str
    decision_hash: str
    snapshot_id: str
    account_id: str
    execution_policy_id: str
    started_at: datetime
    completed_at: datetime
    status: OMSRunStatus
    order_count: int = 0
    fill_count: int = 0
    reconciliation_status: ReconciliationStatus = ReconciliationStatus.NOT_TESTED
    run_hash: str = ""
    order_plan_hash: str = ""
    intent_hash: str = ""
    random_seed: int = 0
    live_trading: bool = False
    note: str = "Paper OMS run. No broker path."


class OMSState(BaseModel):
    model_config = ConfigDict(frozen=True)

    account: PaperAccount
    orders: dict[str, PaperOrder] = Field(default_factory=dict)
    fills: dict[str, PaperFill] = Field(default_factory=dict)
    events: list[OrderEvent] = Field(default_factory=list)
    last_run_id: str = ""
    last_plan_hash: str = ""


class PaperOMSRequest(BaseModel):
    decision_id: str = ""
    account_id: str = "PAPER-001"
    execution_policy_id: str = "base"
    snapshot_id: str = "seed"
    as_of: datetime = Field(default_factory=lambda: datetime(2024, 1, 15, tzinfo=UTC))
    live_trading: bool = False
    allow_short: bool = False
    remainder_fate: RemainderFate = RemainderFate.OPEN
    lot_size: int = 1
    min_trade_quantity: float = 0.0
    cancel_unfilled: bool = False
    data_kind: str = "synthetic"
    future_payload_ignored: dict[str, str] = Field(default_factory=dict)


class TCAReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    gross_target_notional: float = 0.0
    filled_notional: float = 0.0
    spread_drag: float = 0.0
    slippage_drag: float = 0.0
    impact_drag: float = 0.0
    commission: float = 0.0
    other_specified_fees: float = 0.0
    total_execution_drag: float = 0.0
    residual_target: float = 0.0
    implementation_shortfall: float | None = None
    implementation_shortfall_status: CheckResult = CheckResult.NOT_TESTED
    note: str = "Paper TCA. Simulated prices are not broker prints."


class ResetRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    reset_id: str
    previous_state_hash: str
    new_state_hash: str
    reason: str
    timestamp: datetime


class PaperOMSResult(BaseModel):
    run: OMSRun
    decision_id: str
    intents: list[OrderIntent] = Field(default_factory=list)
    plan: OrderPlan
    orders: list[PaperOrder] = Field(default_factory=list)
    fills: list[PaperFill] = Field(default_factory=list)
    events: list[OrderEvent] = Field(default_factory=list)
    account: PaperAccount
    reconciliation: ReconciliationReport
    tca: TCAReport
    exceptions: list[str] = Field(default_factory=list)
    live_trading: bool = False
    note: str = "Paper OMS result. Not live. Not broker-confirmed."
