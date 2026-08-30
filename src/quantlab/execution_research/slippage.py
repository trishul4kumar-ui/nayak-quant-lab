"""Slippage models. BUY must not improve; SELL must not improve."""

from __future__ import annotations

from quantlab.domain.research import CheckResult
from quantlab.execution_research.definition import (
    CostStatus,
    MarketMicrostructureDefinition,
    SlippageKind,
)


def slippage_bps(
    definition: MarketMicrostructureDefinition,
    *,
    spread: float | None,
    volume: float | None,
    trailing_volume: float | None,
    trailing_vol: float | None,
) -> tuple[float | None, CostStatus, CheckResult, str]:
    kind = definition.slippage_model
    if kind is SlippageKind.NONE:
        return 0.0, CostStatus.CONFIGURED, CheckResult.WARN, "zero slippage is optimistic"
    if kind is SlippageKind.FIXED_BPS or kind is SlippageKind.CONFIGURED:
        return (
            float(definition.slippage_bps),
            CostStatus.CONFIGURED,
            CheckResult.PASS,
            "configured slippage; not broker TCA",
        )
    if kind is SlippageKind.SPREAD_FRACTION:
        if spread is None:
            return None, CostStatus.NOT_TESTED, CheckResult.NOT_TESTED, "spread missing"
        return (
            abs(spread) * float(definition.spread_fraction),
            CostStatus.CONFIGURED,
            CheckResult.PASS,
            "slippage as a fraction of spread",
        )
    if kind is SlippageKind.VOL_SCALED:
        if trailing_vol is None:
            return None, CostStatus.NOT_TESTED, CheckResult.NOT_TESTED, "trailing vol missing"
        return (
            float(definition.slippage_bps) * (trailing_vol / 0.01),
            CostStatus.UNCALIBRATED,
            CheckResult.WARN,
            "vol-scaled slippage; uncalibrated",
        )
    if kind is SlippageKind.VOLUME_SCALED:
        if volume is None or trailing_volume is None or volume <= 0:
            return None, CostStatus.NOT_TESTED, CheckResult.NOT_TESTED, "volume missing"
        return (
            float(definition.slippage_bps) * (trailing_volume / volume),
            CostStatus.UNCALIBRATED,
            CheckResult.WARN,
            "volume-scaled slippage; not NSE ADV",
        )
    return None, CostStatus.NOT_TESTED, CheckResult.NOT_TESTED, "unknown slippage model"
