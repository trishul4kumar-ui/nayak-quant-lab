"""Pluggable slippage. None of these is a validated NSE microstructure model."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel


class SlippageModel(Protocol):
    name: str

    def extra_bps(self) -> float | None:
        """Round-trip extra bps, or None if the model cannot be evaluated."""
        ...


class NoSlippage:
    name = "none"

    def extra_bps(self) -> float | None:
        return 0.0


class FixedBpsSlippage:
    name = "fixed_bps"

    def __init__(self, bps: float) -> None:
        if bps < 0:
            raise ValueError("slippage bps cannot be negative")
        self.bps = bps

    def extra_bps(self) -> float | None:
        return self.bps


class SpreadSlippage:
    """Uses a configured spread. Not a live bid/ask feed."""

    name = "spread"

    def __init__(self, spread_bps: float) -> None:
        if spread_bps < 0:
            raise ValueError("spread_bps cannot be negative")
        self.spread_bps = spread_bps

    def extra_bps(self) -> float | None:
        return self.spread_bps


class VolumeParticipationSlippage:
    """Requires ADV. Without liquidity data this model is unevaluable."""

    name = "volume_participation"

    def extra_bps(self) -> float | None:
        return None


class MarketImpactSpec(BaseModel):
    """Interface only. No calibrated impact coefficients ship in this build."""

    name: str = "unspecified"
    status: str = "not_tested"
    note: str = "impact ∝ f(size, ADV, vol, spread); no Indian ADV series is bundled"
