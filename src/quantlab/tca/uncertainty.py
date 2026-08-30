"""Parameter uncertainty. Prefer ranges to false precision."""

from __future__ import annotations


def interval(estimate: float | None, uncertainty: float | None) -> str:
    if estimate is None:
        return "NOT_TESTED"
    if uncertainty is None:
        return f"{estimate:.6g} ± unknown"
    return f"{estimate:.6g} ± {uncertainty:.6g}"
