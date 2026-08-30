"""Long-short factor portfolios from factor scores. Targets, not orders."""

from __future__ import annotations

from quantlab.domain.models import TargetPosition
from quantlab.portfolio.baselines import long_short_top_bottom, targets_to_map


def factor_long_short(
    scores: dict[str, float],
    top_n: int = 2,
    bottom_n: int = 2,
) -> list[TargetPosition]:
    return long_short_top_bottom(scores, top_n, bottom_n)


def factor_weights(
    scores: dict[str, float],
    top_n: int = 2,
    bottom_n: int = 2,
) -> dict[str, float]:
    return targets_to_map(factor_long_short(scores, top_n, bottom_n))
