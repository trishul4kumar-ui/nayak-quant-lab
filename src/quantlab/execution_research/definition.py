"""Versioned execution-research identity. Simulation is not a broker fill."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from quantlab.backtest.costs import CostSchedule
from quantlab.backtest.spec import config_hash
from quantlab.domain.models import Side
from quantlab.domain.research import CheckResult


class SpreadKind(StrEnum):
    FIXED = "fixed"
    VOL_SCALED = "vol_scaled"
    VOLUME_SCALED = "volume_scaled"
    HISTORICAL_BID_ASK = "historical_bid_ask"


class SlippageKind(StrEnum):
    NONE = "none"
    FIXED_BPS = "fixed_bps"
    SPREAD_FRACTION = "spread_fraction"
    VOL_SCALED = "vol_scaled"
    VOLUME_SCALED = "volume_scaled"
    CONFIGURED = "configured"


class ImpactKind(StrEnum):
    NONE = "none"
    FIXED = "fixed"
    SQUARE_ROOT = "square_root"
    PARTICIPATION = "participation"


class LatencyKind(StrEnum):
    ZERO = "zero"
    FIXED = "fixed"
    CONFIGURED = "configured"
    SCENARIO = "scenario"


class FillKind(StrEnum):
    PARTICIPATION_CAPPED = "participation_capped"
    FULL = "full"
    RATIO_CAPPED = "ratio_capped"


class LiquidityKind(StrEnum):
    BAR_VOLUME = "bar_volume"
    UNKNOWN = "unknown"


class FillStatus(StrEnum):
    FULLY_FILLED = "fully_filled"
    PARTIALLY_FILLED = "partially_filled"
    UNFILLED = "unfilled"


class CostStatus(StrEnum):
    CALIBRATED = "calibrated"
    CONFIGURED = "configured"
    UNSPECIFIED = "unspecified"
    NOT_TESTED = "not_tested"
    UNCALIBRATED = "uncalibrated"


class ProvenanceStatus(StrEnum):
    CONFIGURED = "configured"
    SYNTHETIC = "synthetic"
    UNCALIBRATED = "uncalibrated"
    NOT_TESTED = "not_tested"


class MarketMicrostructureDefinition(BaseModel):
    definition_id: str
    version: str
    name: str
    spread_model: SpreadKind = SpreadKind.FIXED
    spread_bps: float = 5.0
    tick_size: float = 0.05
    bid_ask_availability: str = "unavailable"
    volume_model: str = "bar_volume"
    liquidity_model: LiquidityKind = LiquidityKind.BAR_VOLUME
    impact_model: ImpactKind = ImpactKind.NONE
    impact_bps: float = 0.0
    impact_k: float = 0.1
    latency_model: LatencyKind = LatencyKind.ZERO
    latency_sessions: int = 0
    fill_model: FillKind = FillKind.PARTICIPATION_CAPPED
    participation_model: str = "max_participation"
    max_participation: float = 0.20
    fill_ratio_cap: float = 1.0
    slippage_model: SlippageKind = SlippageKind.FIXED_BPS
    slippage_bps: float = 2.0
    spread_fraction: float = 0.5
    vol_lookback: int = 20
    adv_lookback: int = 20
    seed: int = 0
    cost: CostSchedule = Field(default_factory=CostSchedule)
    parameter_provenance: str = "configured_research_defaults"
    snapshot_id: str = ""
    notes: str = (
        "Simulated fills are not broker-confirmed. Synthetic volume is not NSE ADV. "
        "Uncalibrated impact is not market evidence."
    )
    implementation_version: str = "1.3.0"

    def identity_hash(self) -> str:
        return config_hash(
            {
                "definition_id": self.definition_id,
                "version": self.version,
                "spread_model": self.spread_model.value,
                "spread_bps": self.spread_bps,
                "tick_size": self.tick_size,
                "liquidity_model": self.liquidity_model.value,
                "impact_model": self.impact_model.value,
                "impact_bps": self.impact_bps,
                "impact_k": self.impact_k,
                "latency_model": self.latency_model.value,
                "latency_sessions": self.latency_sessions,
                "fill_model": self.fill_model.value,
                "max_participation": self.max_participation,
                "fill_ratio_cap": self.fill_ratio_cap,
                "slippage_model": self.slippage_model.value,
                "slippage_bps": self.slippage_bps,
                "spread_fraction": self.spread_fraction,
                "vol_lookback": self.vol_lookback,
                "adv_lookback": self.adv_lookback,
                "seed": self.seed,
                "cost": self.cost.model_dump(mode="json"),
            }
        )


class ExecutionLeakFlags(BaseModel):
    future_volume: bool = False
    future_spread: bool = False
    future_liquidity: bool = False
    future_impact_parameter: bool = False
    future_execution_parameter: bool = False
    future_latency: bool = False
    pre_arrival_fill: bool = False
    full_fill: bool = False
    wrong_side_slippage: bool = False
    wrong_side_impact: bool = False
    hidden_partial_fill: bool = False
    capacity_lookahead: bool = False
    future_calibration: bool = False
    model_mutation: bool = False


class OrderIntent(BaseModel):
    intent_id: str
    decision_time: datetime
    security_id: str
    side: Side
    target_quantity: float
    reference_price: float
    portfolio_id: str = ""
    strategy_id: str = "cs_momentum_v1"
    alpha_id: str = ""
    model_id: str = ""
    ensemble_id: str = ""
    urgency: str = "session"
    max_participation: float = 0.2
    limit_price: float | None = None
    time_in_force: str = "day"
    note: str = "research object; not sent to a broker"


class CostComponent(BaseModel):
    name: str
    value: float
    unit: str = "currency"
    provenance: str = "configured"
    status: CostStatus = CostStatus.CONFIGURED


class SimulatedFill(BaseModel):
    fill_id: str
    intent_id: str
    security_id: str
    timestamp: datetime
    side: Side
    quantity: float
    requested_quantity: float
    remaining_quantity: float
    fill_ratio: float
    reference_price: float
    execution_price: float
    spread_bps: float = 0.0
    slippage_bps: float = 0.0
    impact_bps: float = 0.0
    explicit_bps: float = 0.0
    spread_cost: float = 0.0
    slippage_cost: float = 0.0
    impact_cost: float = 0.0
    explicit_cost: float = 0.0
    total_cost: float = 0.0
    fill_status: FillStatus = FillStatus.UNFILLED
    participation: float | None = None
    available_volume: float | None = None
    model_id: str = ""
    arrival_time: datetime | None = None
    regime: str | None = None
    data_kind: str = "synthetic"
    status: CheckResult = CheckResult.WARN
    note: str = "simulated fill; not a broker confirmation"


class LiquidityProfile(BaseModel):
    security_id: str
    as_of: datetime
    session_volume: float | None = None
    trailing_volume: float | None = None
    participation_limit: float
    liquidity_bucket: str = "synthetic"
    capacity_status: str = "not_tested"
    note: str = "synthetic bar volume is not official NSE ADV"


class ExecutionFragility(BaseModel):
    schema_version: str = "1"
    formula_id: str = "fragility_v1"
    score: float
    flags: list[str] = Field(default_factory=list)
    note: str = (
        "Deterministic research metric, not a calibrated probability. "
        "formula: clip(0.4*cost_stress_ratio + 0.3*(1-fill_ratio) + 0.3*min(latency/5,1), 0, 1)"
    )
