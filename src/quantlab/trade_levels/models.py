"""Immutable contracts for deterministic trade-level research artifacts."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self
from uuid import uuid4

from pydantic import AwareDatetime, Field, model_validator

from quantlab.agents.hashing import Artifact


class TradeDirection(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"


class LevelArchetype(StrEnum):
    BREAKOUT = "BREAKOUT"
    PULLBACK = "PULLBACK"
    LIMIT_ZONE = "LIMIT_ZONE"
    MOMENTUM_CONTINUATION = "MOMENTUM_CONTINUATION"
    MEAN_REVERSION_RECOVERY = "MEAN_REVERSION_RECOVERY"
    BREAKDOWN = "BREAKDOWN"
    FAILED_BREAKOUT = "FAILED_BREAKOUT"
    VOLATILITY_TRIGGER = "VOLATILITY_TRIGGER"
    NO_VALID_ENTRY = "NO_VALID_ENTRY"


class PriceBasis(StrEnum):
    ADJUSTED = "ADJUSTED"
    RAW = "RAW"


class LevelPlanStatus(StrEnum):
    READY = "READY"
    NO_VALID_ENTRY = "NO_VALID_ENTRY"


class FreshnessStatus(StrEnum):
    FRESH = "FRESH"
    STALE_LEVEL_PLAN = "STALE_LEVEL_PLAN"


class ExitRuleName(StrEnum):
    HARD_INVALIDATION = "HARD_INVALIDATION"
    PROTECTIVE_STOP = "PROTECTIVE_STOP"
    PROFIT_TARGET = "PROFIT_TARGET"
    TRAILING_STOP = "TRAILING_STOP"
    TIME_STOP = "TIME_STOP"
    REGIME_EXIT = "REGIME_EXIT"
    FACTOR_DETERIORATION_EXIT = "FACTOR_DETERIORATION_EXIT"
    LIQUIDITY_EXIT = "LIQUIDITY_EXIT"
    VOLATILITY_SHOCK_EXIT = "VOLATILITY_SHOCK_EXIT"
    MODEL_CONFIDENCE_DECAY_EXIT = "MODEL_CONFIDENCE_DECAY_EXIT"
    SESSION_EXIT = "SESSION_EXIT"


class TradeLevelPolicy(Artifact):
    policy_id: str
    entry_band_atr: float = Field(gt=0, le=1)
    protective_stop_atr: float = Field(gt=0, le=10)
    hard_invalidation_atr: float = Field(gt=0, le=10)
    target_atr_multiples: tuple[float, ...] = Field(min_length=1, max_length=4)
    trailing_atr: float = Field(gt=0, le=10)
    max_price_move_bps: float = Field(gt=0, le=5_000)
    max_volatility_change_ratio: float = Field(gt=0, le=10)
    max_snapshot_age_seconds: int = Field(gt=0, le=86_400)

    @model_validator(mode="after")
    def coherent_distances(self) -> Self:
        if self.hard_invalidation_atr <= self.protective_stop_atr:
            raise ValueError("hard invalidation must be farther than the protective stop")
        if tuple(sorted(self.target_atr_multiples)) != self.target_atr_multiples:
            raise ValueError("targets must be ordered")
        return self


class ExitRule(Artifact):
    rule: ExitRuleName
    condition: str = Field(min_length=1, max_length=500)
    version: str = Field(min_length=1, max_length=80)


class ExitPolicy(Artifact):
    policy_id: str
    direction: TradeDirection
    rules: tuple[ExitRule, ...] = Field(min_length=1, max_length=16)

    @model_validator(mode="after")
    def unique_rules(self) -> Self:
        if len({rule.rule for rule in self.rules}) != len(self.rules):
            raise ValueError("exit rules must be unique")
        return self


class TradeLevelInput(Artifact):
    """Caller-supplied canonical inputs. No values are inferred or fetched here."""

    adjudication_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    adjudication_outcome: Literal["BULL_DOMINANT", "BEAR_DOMINANT"]
    adjudication_no_trade: Literal[False] = False
    snapshot_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    security_id: str = Field(min_length=1, max_length=160)
    direction: TradeDirection
    archetype: LevelArchetype
    as_of: AwareDatetime
    expires_at: AwareDatetime
    reference_price: float = Field(gt=0)
    atr: float | None = Field(default=None, gt=0)
    support_price: float | None = Field(default=None, gt=0)
    resistance_price: float | None = Field(default=None, gt=0)
    bid_price: float | None = Field(default=None, gt=0)
    ask_price: float | None = Field(default=None, gt=0)
    spread_bps: float | None = Field(default=None, ge=0)
    regime: str = Field(min_length=1, max_length=120)
    price_basis: PriceBasis
    quote_price_basis: PriceBasis
    adjustment_policy_id: str = Field(min_length=1, max_length=160)
    tick_size: float = Field(gt=0)
    market_session: str = Field(min_length=1, max_length=80)
    data_quality: Literal["valid"]
    data_freshness: Literal["fresh"]

    @model_validator(mode="after")
    def input_integrity(self) -> Self:
        if self.created_at < self.as_of or self.expires_at <= self.as_of:
            raise ValueError("level input clocks are invalid")
        if self.price_basis is not self.quote_price_basis:
            raise ValueError("adjusted history and quote price basis must match")
        if (self.bid_price is None) != (self.ask_price is None):
            raise ValueError("bid and ask must be supplied together")
        if (
            self.bid_price is not None
            and self.ask_price is not None
            and self.bid_price > self.ask_price
        ):
            raise ValueError("bid cannot exceed ask")
        if self.archetype is not LevelArchetype.NO_VALID_ENTRY and self.atr is None:
            raise ValueError("approved volatility input is required")
        return self


class TradeLevelPlan(Artifact):
    plan_id: str = Field(default_factory=lambda: uuid4().hex)
    status: LevelPlanStatus
    security_id: str
    direction: TradeDirection
    as_of: AwareDatetime
    expires_at: AwareDatetime
    snapshot_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    adjudication_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    archetype: LevelArchetype
    entry_zone_low: float | None = Field(default=None, gt=0)
    entry_zone_high: float | None = Field(default=None, gt=0)
    preferred_reference_price: float | None = Field(default=None, gt=0)
    hard_invalidation: float | None = Field(default=None, gt=0)
    protective_stop: float | None = Field(default=None, gt=0)
    targets: tuple[float, ...] = Field(default=(), max_length=4)
    trailing_rule: str | None = Field(default=None, max_length=300)
    time_stop: str | None = Field(default=None, max_length=200)
    max_holding_period: str | None = Field(default=None, max_length=200)
    price_basis: PriceBasis
    tick_size: float = Field(gt=0)
    adjustment_policy_id: str
    required_market_state: tuple[str, ...]
    warnings: tuple[str, ...]
    not_tested: tuple[str, ...]
    level_policy_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    exit_policy_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    reference_atr: float | None = Field(default=None, gt=0)
    reference_regime: str | None = None
    execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def coherent_plan(self) -> Self:
        numeric = (
            self.entry_zone_low,
            self.entry_zone_high,
            self.preferred_reference_price,
            self.hard_invalidation,
            self.protective_stop,
        )
        if self.status is LevelPlanStatus.NO_VALID_ENTRY:
            if any(value is not None for value in numeric) or self.targets or self.exit_policy_hash:
                raise ValueError("no-entry plans cannot contain tradable levels")
            return self
        if any(value is None for value in numeric) or not self.targets or not self.exit_policy_hash:
            raise ValueError("ready plan requires complete deterministic levels")
        if any(target <= 0 for target in self.targets):
            raise ValueError("targets must be positive prices")
        assert self.entry_zone_low is not None and self.entry_zone_high is not None
        assert self.hard_invalidation is not None and self.protective_stop is not None
        if self.entry_zone_low > self.entry_zone_high:
            raise ValueError("entry zone is inverted")
        if self.direction is TradeDirection.LONG:
            if not self.hard_invalidation < self.protective_stop < self.entry_zone_low:
                raise ValueError("long stop/invalidation direction is impossible")
            if any(target <= self.entry_zone_high for target in self.targets):
                raise ValueError("long targets must exceed entry")
        elif not self.hard_invalidation > self.protective_stop > self.entry_zone_high:
            raise ValueError("short stop/invalidation direction is impossible")
        elif any(target >= self.entry_zone_low for target in self.targets):
            raise ValueError("short targets must be below entry")
        return self


class PlanFreshness(Artifact):
    plan_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    status: FreshnessStatus
    reasons: tuple[str, ...]
    current_price: float = Field(gt=0)
    current_atr: float = Field(gt=0)
    current_regime: str = Field(min_length=1, max_length=120)


class TradeChartOverlayDTO(Artifact):
    """Presentation-only DTO for a native or local chart renderer."""

    plan_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    entry_zone_low: float | None = Field(default=None, gt=0)
    entry_zone_high: float | None = Field(default=None, gt=0)
    hard_invalidation: float | None = Field(default=None, gt=0)
    protective_stop: float | None = Field(default=None, gt=0)
    targets: tuple[float, ...] = ()
    trailing_rule: str | None = None
    time_horizon: str | None = None
    evidence_markers: tuple[str, ...] = ()
