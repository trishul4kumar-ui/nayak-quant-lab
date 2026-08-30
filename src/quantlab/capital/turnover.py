"""Turnover budget. Reuses Prompt 07 two-sided L1 convention. Targets only."""

from __future__ import annotations

from quantlab.portfolio.turnover import two_sided_turnover


def estimate_turnover(previous: dict[str, float], proposed: dict[str, float]) -> float:
    return two_sided_turnover(previous, proposed)


def apply_band(
    previous: dict[str, float], proposed: dict[str, float], band: float
) -> dict[str, float]:
    if band <= 0:
        return dict(proposed)
    names = sorted(set(previous) | set(proposed))
    out: dict[str, float] = {}
    for name in names:
        old = previous.get(name, 0.0)
        new = proposed.get(name, 0.0)
        out[name] = old if abs(new - old) < band else new
    return {k: v for k, v in out.items() if abs(v) > 0}


def apply_min_trade(
    previous: dict[str, float], proposed: dict[str, float], threshold: float
) -> dict[str, float]:
    if threshold <= 0:
        return dict(proposed)
    names = sorted(set(previous) | set(proposed))
    out: dict[str, float] = {}
    for name in names:
        old = previous.get(name, 0.0)
        new = proposed.get(name, 0.0)
        out[name] = old if abs(new - old) < threshold else new
    return {k: v for k, v in out.items() if abs(v) > 0}
