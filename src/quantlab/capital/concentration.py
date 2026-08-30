"""Concentration diagnostics. Hard limits are enforced elsewhere and never relaxed here."""

from __future__ import annotations


def herfindahl(weights: dict[str, float]) -> float:
    return sum(w * w for w in weights.values())


def effective_n(weights: dict[str, float]) -> float:
    hhi = herfindahl(weights)
    if hhi <= 0:
        return 0.0
    return 1.0 / hhi


def top_k_weight(weights: dict[str, float], k: int) -> float:
    ordered = sorted((abs(w) for w in weights.values()), reverse=True)
    return sum(ordered[:k])


def max_name_weight(weights: dict[str, float]) -> float:
    if not weights:
        return 0.0
    return max(abs(w) for w in weights.values())
