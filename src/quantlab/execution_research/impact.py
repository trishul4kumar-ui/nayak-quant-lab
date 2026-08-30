"""Market impact. Coefficients are UNCALIBRATED unless proven otherwise."""

from __future__ import annotations

from quantlab.domain.research import CheckResult
from quantlab.execution_research.definition import (
    CostStatus,
    ImpactKind,
    MarketMicrostructureDefinition,
)


def impact_bps(
    definition: MarketMicrostructureDefinition,
    *,
    quantity: float,
    volume: float | None,
    trailing_vol: float | None,
) -> tuple[float | None, CostStatus, CheckResult, str]:
    kind = definition.impact_model
    if kind is ImpactKind.NONE:
        return 0.0, CostStatus.CONFIGURED, CheckResult.WARN, "zero impact is a research assumption"
    if kind is ImpactKind.FIXED:
        return (
            float(definition.impact_bps),
            CostStatus.UNCALIBRATED,
            CheckResult.WARN,
            "fixed impact bps; not calibrated to NSE",
        )
    if volume is None or volume <= 0:
        return (
            None,
            CostStatus.NOT_TESTED,
            CheckResult.NOT_TESTED,
            "volume missing; impact not applied as 0",
        )
    participation = quantity / volume
    if kind is ImpactKind.SQUARE_ROOT:
        if trailing_vol is None:
            return (
                None,
                CostStatus.NOT_TESTED,
                CheckResult.NOT_TESTED,
                "vol missing for square-root impact",
            )
        value = (
            float(definition.impact_k) * trailing_vol * (max(participation, 0.0) ** 0.5) * 10_000.0
        )
        return (
            value,
            CostStatus.UNCALIBRATED,
            CheckResult.WARN,
            "square-root impact ∝ vol × sqrt(q/V); UNCALIBRATED",
        )
    if kind is ImpactKind.PARTICIPATION:
        value = float(definition.impact_k) * participation * 10_000.0
        return (
            value,
            CostStatus.UNCALIBRATED,
            CheckResult.WARN,
            "participation impact ∝ q/V; UNCALIBRATED",
        )
    return None, CostStatus.NOT_TESTED, CheckResult.NOT_TESTED, "unknown impact model"
