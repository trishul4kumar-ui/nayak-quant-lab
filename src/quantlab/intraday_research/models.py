"""PIT intraday and scalp-research contracts. They cannot represent a live order."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self

from pydantic import AwareDatetime, Field, model_validator

from quantlab.agents.hashing import Artifact


class ArrivalState(StrEnum):
    VALID = "VALID"
    DUPLICATE = "DUPLICATE"
    OUT_OF_ORDER = "OUT_OF_ORDER"
    GAP = "GAP"
    STALE = "STALE"
    MISSING_DEPTH = "MISSING_DEPTH"


class ResearchClass(StrEnum):
    HUMAN_REVIEWABLE_INTRADAY = "HUMAN_REVIEWABLE_INTRADAY"
    AUTOMATION_RESEARCH_ONLY = "AUTOMATION_RESEARCH_ONLY"


class DepthLevel(Artifact):
    price: float = Field(gt=0)
    quantity: float = Field(ge=0)


class DepthSnapshot(Artifact):
    bids: tuple[DepthLevel, ...] = Field(min_length=1, max_length=5)
    asks: tuple[DepthLevel, ...] = Field(min_length=1, max_length=5)

    @model_validator(mode="after")
    def coherent_book(self) -> Self:
        if self.bids[0].price >= self.asks[0].price:
            raise ValueError("crossed or locked book cannot create a scalp signal")
        return self


class TickObservation(Artifact):
    security_id: str = Field(min_length=1, max_length=160)
    provider_timestamp: AwareDatetime | None = None
    exchange_timestamp: AwareDatetime | None = None
    last_trade_timestamp: AwareDatetime | None = None
    received_at: AwareDatetime
    processed_at: AwareDatetime
    price: float = Field(gt=0)
    quantity: float | None = Field(default=None, ge=0)
    provider_sequence: int | None = Field(default=None, ge=0)
    depth: DepthSnapshot | None = None
    arrival_state: ArrivalState
    live_trading: Literal[False] = False

    @model_validator(mode="after")
    def pit_clock(self) -> Self:
        if self.processed_at < self.received_at:
            raise ValueError("processed timestamp cannot predate receipt")
        return self


class MicrostructureSnapshot(Artifact):
    tick_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    spread: float | None = Field(default=None, gt=0)
    relative_spread_bps: float | None = Field(default=None, ge=0)
    microprice: float | None = Field(default=None, gt=0)
    top_imbalance: float | None = Field(default=None, ge=-1, le=1)
    quality: ArrivalState


class ScalpStrategyDefinition(Artifact):
    strategy_id: str = Field(min_length=1, max_length=160)
    version: str = Field(min_length=1, max_length=80)
    required_features: tuple[str, ...] = Field(min_length=1, max_length=20)
    entry_threshold: float = Field(gt=0, le=1)
    maximum_spread_bps: float = Field(gt=0, le=1_000)
    horizon_seconds: int = Field(ge=1, le=86_400)
    research_class: ResearchClass
    cost_model_version: str = Field(min_length=1, max_length=160)
    max_orders_per_interval: int = Field(ge=0, le=100)
    execution_authority: Literal[False] = False


class ScalpSignal(Artifact):
    strategy_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    snapshot_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    direction: Literal["LONG", "BEARISH", "ABSTAIN"]
    reason: str = Field(min_length=1, max_length=300)
    quality: ArrivalState
    execution_authority: Literal[False] = False
