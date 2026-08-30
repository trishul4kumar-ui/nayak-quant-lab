"""Adaptive ensemble weights. Hard constraints are not silently relaxed."""

from __future__ import annotations

from quantlab.adaptive.definition import AdaptiveModelDefinition
from quantlab.core.errors import InfeasibleAdaptiveEnsemble


def constrain_weights(
    weights: dict[str, float],
    model: AdaptiveModelDefinition,
) -> tuple[dict[str, float], bool]:
    names = sorted(weights)
    if not names:
        raise InfeasibleAdaptiveEnsemble("no component weights")
    if model.min_alpha_weight * len(names) > 1.0 + 1e-12:
        raise InfeasibleAdaptiveEnsemble("min_alpha_weight * n_alphas > 1")
    raw = [max(float(weights[name]), 0.0) for name in names]
    total = sum(raw)
    fallback = False
    if total <= 0:
        raw = [1.0 for _ in names]
        total = float(len(names))
        fallback = True
    clipped = [
        min(max(value / total, model.min_alpha_weight), model.max_alpha_weight) for value in raw
    ]
    clipped_total = sum(clipped)
    if clipped_total <= 0:
        raise InfeasibleAdaptiveEnsemble("weights vanished after clipping")
    out = [value / clipped_total for value in clipped]
    if any(value > model.max_alpha_weight + 1e-9 for value in out):
        raise InfeasibleAdaptiveEnsemble("max_alpha_weight infeasible after renormalization")
    hhi = sum(value * value for value in out)
    if hhi > model.max_concentration + 1e-12:
        raise InfeasibleAdaptiveEnsemble("max_concentration")
    active = sum(1 for value in out if value > 1e-12)
    if active < model.min_active_alphas:
        raise InfeasibleAdaptiveEnsemble("min_active_alphas")
    return dict(zip(names, out, strict=True)), fallback
