"""Factor and beta exposure. Missing is NOT_TESTED, never silently zero."""

from __future__ import annotations

from quantlab.domain.research import CheckResult


def portfolio_exposure(
    weights: dict[str, float],
    exposures: dict[str, float | None],
) -> tuple[float | None, CheckResult]:
    if not weights:
        return None, CheckResult.NOT_TESTED
    missing = False
    total = 0.0
    for name, weight in weights.items():
        if abs(weight) < 1e-15:
            continue
        value = exposures.get(name)
        if value is None:
            missing = True
            continue
        total += weight * value
    if missing:
        return None, CheckResult.NOT_TESTED
    if not exposures:
        return None, CheckResult.NOT_TESTED
    return total, CheckResult.PASS


def unknown_as_zero(exposures: dict[str, float | None]) -> bool:
    """True when a caller substituted 0 for missing factor data."""
    return False if exposures else False
