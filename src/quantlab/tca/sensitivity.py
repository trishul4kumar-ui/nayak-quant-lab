"""Sensitivity of shortfall to cost multipliers. Diagnostic only."""

from __future__ import annotations

from quantlab.tca.models import ShortfallBreakdown


def scale_shortfall(item: ShortfallBreakdown, factor: float) -> float | None:
    if item.total is None:
        return None
    return item.total * factor
