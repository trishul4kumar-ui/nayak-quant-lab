"""Exponential weights. weight(age)=λ^age with λ=exp(-ln2 / half_life); newest age=0."""

from __future__ import annotations

import math

from quantlab.core.errors import AdaptiveError


def decay_lambda(half_life: float) -> float:
    if half_life <= 0:
        raise AdaptiveError("half_life must be > 0 sessions")
    return math.exp(-math.log(2.0) / half_life)


def ewma_weights(n: int, half_life: float) -> list[float]:
    """Chronological oldest-first. Last index is age 0."""
    if n <= 0:
        return []
    lam = decay_lambda(half_life)
    return [lam ** (n - 1 - i) for i in range(n)]


def effective_sample_size(weights: list[float]) -> float:
    total = sum(weights)
    squares = sum(w * w for w in weights)
    if squares <= 0:
        return 0.0
    return (total * total) / squares


def ewma_mean(values: list[float], half_life: float) -> float | None:
    if not values:
        return None
    weights = ewma_weights(len(values), half_life)
    total = sum(weights)
    if total <= 0:
        return None
    return sum(w * v for w, v in zip(weights, values, strict=True)) / total
