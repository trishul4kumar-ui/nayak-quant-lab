"""Spread models. Missing bid/ask is NOT_TESTED, never a silent 0."""

from __future__ import annotations

from quantlab.domain.research import CheckResult
from quantlab.execution_research.definition import (
    CostStatus,
    MarketMicrostructureDefinition,
    SpreadKind,
)


def spread_bps(
    definition: MarketMicrostructureDefinition,
    *,
    volume: float | None,
    trailing_volume: float | None,
    trailing_vol: float | None,
    future_spread_bps: float | None = None,
    use_future_spread: bool = False,
) -> tuple[float | None, CostStatus, CheckResult, str]:
    if use_future_spread:
        if future_spread_bps is None:
            return (
                None,
                CostStatus.NOT_TESTED,
                CheckResult.FAIL,
                "future spread requested but missing",
            )
        return (
            float(future_spread_bps),
            CostStatus.CONFIGURED,
            CheckResult.FAIL,
            "future_spread_leak",
        )
    kind = definition.spread_model
    if kind is SpreadKind.HISTORICAL_BID_ASK:
        return (
            None,
            CostStatus.NOT_TESTED,
            CheckResult.NOT_TESTED,
            "no PIT bid/ask dump; historical spread is NOT_TESTED",
        )
    if kind is SpreadKind.FIXED:
        return (
            float(definition.spread_bps),
            CostStatus.CONFIGURED,
            CheckResult.PASS,
            "configured fixed spread; not calibrated NSE quotes",
        )
    if kind is SpreadKind.VOL_SCALED:
        if trailing_vol is None:
            return None, CostStatus.NOT_TESTED, CheckResult.NOT_TESTED, "trailing vol missing"
        scale = trailing_vol / 0.01
        return (
            float(definition.spread_bps) * max(scale, 0.0),
            CostStatus.UNCALIBRATED,
            CheckResult.WARN,
            "vol-scaled spread; coefficient uncalibrated",
        )
    if kind is SpreadKind.VOLUME_SCALED:
        if volume is None or trailing_volume is None or volume <= 0:
            return None, CostStatus.NOT_TESTED, CheckResult.NOT_TESTED, "volume missing"
        scale = trailing_volume / volume
        return (
            float(definition.spread_bps) * max(scale, 0.0),
            CostStatus.UNCALIBRATED,
            CheckResult.WARN,
            "volume-scaled spread; not official ADV",
        )
    return None, CostStatus.NOT_TESTED, CheckResult.NOT_TESTED, "unknown spread model"
