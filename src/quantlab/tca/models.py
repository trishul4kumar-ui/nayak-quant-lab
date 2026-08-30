"""Frozen TCA domain types. Modelled costs are never labelled realized."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from quantlab.domain.research import CheckResult
from quantlab.tca.enums import (
    ArrivalPolicy,
    CapacityStatus,
    FragilityStatus,
    SpreadKind,
    TCAKind,
)


class CostLeg(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    value: float | None
    status: CheckResult
    provenance: str
    note: str = ""


class ShortfallBreakdown(BaseModel):
    model_config = ConfigDict(frozen=True)

    delay_cost: float | None = None
    trading_cost: float | None = None
    spread_cost: float | None = None
    market_impact: float | None = None
    opportunity_cost: float | None = None
    explicit_fees: float | None = None
    total: float | None = None
    status: CheckResult = CheckResult.NOT_TESTED
    definition_version: str = "is-v1"
    note: str = "IS = delay + trading + spread + impact + opportunity + fees."


class CalibrationRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    model_id: str
    model_version: str
    method: str
    fit_window_start: datetime
    fit_window_end: datetime
    snapshot_id: str
    sample_count: int
    estimate: float | None
    uncertainty: float | None
    parameter_hash: str = ""
    data_checksum: str = ""
    validation: CheckResult = CheckResult.NOT_TESTED
    frozen: bool = False
    note: str = "CALIBRATE → FREEZE → TEST. Never fit on all data then replay."


class CapacityPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    policy_id: str
    max_participation: float
    max_cost_bps: float
    min_net_edge: float
    note: str = "Capacity is not 'largest capital with a positive backtest'."


class CapacityScenario(BaseModel):
    model_config = ConfigDict(frozen=True)

    capital: float
    participation: float | None
    estimated_impact_bps: float | None
    expected_cost: float | None
    net_edge: float | None
    turnover: float | None
    unfilled: float | None
    breach: bool
    note: str = "Scenario size, not a claim."


class CapacityResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    policy_id: str
    status: CapacityStatus
    scenarios: list[CapacityScenario] = Field(default_factory=list)
    max_feasible_capital: float | None = None
    note: str = "Synthetic volume is not NSE ADV. Missing volume → NOT_TESTED."


class FragilityResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: FragilityStatus
    surface: dict[str, float] = Field(default_factory=dict)
    note: str = "Fragility is not a promotion decision. Prompt 05 remains the gate."


class LiquidityObservation(BaseModel):
    model_config = ConfigDict(frozen=True)

    volume: float | None = None
    participation: float | None = None
    spread: float | None = None
    status: CheckResult = CheckResult.NOT_TESTED
    note: str = "Do not call synthetic volume NSE ADV."


class TCARun(BaseModel):
    model_config = ConfigDict(frozen=True)

    tca_run_id: str
    oms_run_id: str
    kind: TCAKind
    arrival_policy: ArrivalPolicy
    as_of: datetime
    tca_hash: str = ""
    calibration_hash: str = ""
    live_trading: bool = False
    note: str = "Research TCA. Not a broker execution report."


class TCARequest(BaseModel):
    oms_run_id: str = "last"
    kind: TCAKind = TCAKind.OBSERVED
    arrival_policy: ArrivalPolicy = ArrivalPolicy.ARRIVAL_SNAPSHOT
    live_trading: bool = False
    data_kind: str = "synthetic"
    as_of: datetime = Field(default_factory=lambda: datetime(2024, 1, 15, tzinfo=UTC))
    future_payload_ignored: dict[str, str] = Field(default_factory=dict)
    calibrate: bool = False
    capacity_policy: CapacityPolicy | None = None
    user_benchmark_price: float | None = None


class TCAResult(BaseModel):
    run: TCARun
    kind: TCAKind
    shortfall: ShortfallBreakdown
    spread_kind: SpreadKind
    costs: list[CostLeg] = Field(default_factory=list)
    liquidity: LiquidityObservation
    calibration: CalibrationRecord | None = None
    capacity: CapacityResult
    fragility: FragilityResult
    paper_comparison: dict[str, float] = Field(default_factory=dict)
    live_trading: bool = False
    note: str = "Observed vs modelled TCA are distinct. Paper fill ≠ broker confirmation."
