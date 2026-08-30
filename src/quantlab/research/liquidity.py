"""Liquidity filters. Without ADV/spread data the check is NOT_TESTED."""

from __future__ import annotations

from pydantic import BaseModel

from quantlab.domain.research import CheckResult


class LiquidityConstraint(BaseModel):
    min_adv: float | None = None
    max_participation: float | None = None
    min_price: float | None = None
    provenance: str = "unspecified"


class LiquidityReport(BaseModel):
    schema_version: str = "1"
    status: CheckResult = CheckResult.NOT_TESTED
    note: str = "ADV/spread/market-cap series are not bundled; infinite liquidity is not assumed"


def evaluate_liquidity(constraint: LiquidityConstraint | None = None) -> LiquidityReport:
    if constraint is None or constraint.min_adv is None:
        return LiquidityReport()
    return LiquidityReport(
        status=CheckResult.NOT_TESTED,
        note="constraint recorded but ADV data is unavailable",
    )
