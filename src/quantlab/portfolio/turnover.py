"""Two-sided turnover. Same convention as the next-bar backtester."""

from __future__ import annotations


def two_sided_turnover(prev: dict[str, float], new: dict[str, float]) -> float:
    """0.5 × Σ |w_target − w_pretrade|. Non-negative."""
    keys = set(prev) | set(new)
    return 0.5 * sum(abs(new.get(k, 0.0) - prev.get(k, 0.0)) for k in keys)
