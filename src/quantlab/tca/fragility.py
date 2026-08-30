"""Execution fragility surface. Not a research-gate outcome."""

from __future__ import annotations

from quantlab.tca.enums import FragilityStatus
from quantlab.tca.models import CapacityResult, FragilityResult, ShortfallBreakdown


def fragility_from(
    shortfall: ShortfallBreakdown,
    capacity: CapacityResult,
    *,
    stressed_cost_mult: float = 2.0,
) -> FragilityResult:
    total = shortfall.total
    surface = {
        "base_shortfall": total or 0.0,
        "stressed_shortfall": (total or 0.0) * stressed_cost_mult,
        "capacity_breaches": float(sum(1 for row in capacity.scenarios if row.breach)),
    }
    if total is None or capacity.status.value == "not_tested":
        status = FragilityStatus.NOT_TESTED
    elif capacity.status.value == "breach" or (
        total is not None and total > 0 and stressed_cost_mult >= 3
    ):
        status = FragilityStatus.ECONOMICALLY_UNVIABLE
    elif surface["capacity_breaches"] >= 4:
        status = FragilityStatus.FRAGILE
    else:
        status = FragilityStatus.ROBUST
    return FragilityResult(status=status, surface=surface)
