"""Combine signed, PIT-normalized component scores. Reuses Prompt 07 combiners."""

from __future__ import annotations

from quantlab.alpha.combinations import (
    linear_combo,
    rank_average,
    rank_sum,
    weighted_zscore,
    zscore_map,
)
from quantlab.ensemble.definition import CombinationMethod, EnsembleDefinition, Normalization
from quantlab.features.engine import Panel
from quantlab.math.metrics import cross_sectional_ranks


def normalize_row(
    values: dict[str, float],
    method: Normalization,
    *,
    global_mean: float | None = None,
    global_std: float | None = None,
) -> dict[str, float]:
    if not values:
        return {}
    if method is Normalization.RAW:
        return dict(values)
    if method is Normalization.RANK:
        return cross_sectional_ranks(values)
    if method is Normalization.RANK_ZSCORE:
        return zscore_map(cross_sectional_ranks(values))
    if global_mean is not None and global_std is not None and global_std > 0:
        return {key: (val - global_mean) / global_std for key, val in values.items()}
    if method in {Normalization.ZSCORE, Normalization.CS_ZSCORE, Normalization.VOL_SCALED}:
        return zscore_map(values)
    return zscore_map(values)


def pooled_moments(panel: Panel) -> tuple[float | None, float | None]:
    values: list[float] = []
    for row in panel.values():
        values.extend(row.values())
    if len(values) < 2:
        return None, None
    mean = sum(values) / len(values)
    var = sum((v - mean) ** 2 for v in values) / len(values)
    std = var**0.5
    return mean, None if std <= 0 else std


def combine_at(
    definition: EnsembleDefinition,
    rows: list[dict[str, float]],
    weights: list[float],
) -> dict[str, float]:
    if not rows:
        return {}
    method = definition.combination_method
    if method is CombinationMethod.RANK_SUM:
        return rank_sum(rows)
    if method is CombinationMethod.RANK_AVERAGE:
        return rank_average(rows)
    if method is CombinationMethod.LINEAR:
        return linear_combo(rows, weights)
    if method in {CombinationMethod.STACKING, CombinationMethod.META_ALPHA}:
        return linear_combo(rows, weights)
    return weighted_zscore(rows, weights)


def signed_row(row: dict[str, float], direction: int) -> dict[str, float]:
    return {key: direction * value for key, value in row.items()}
