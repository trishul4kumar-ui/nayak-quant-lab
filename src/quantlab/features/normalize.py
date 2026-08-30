"""Cross-sectional transforms at T using only names and values available at T."""

from __future__ import annotations

import numpy as np

from quantlab.features.definition import NormalizationMethod
from quantlab.math.metrics import cross_sectional_ranks, zscore


def percentile_ranks(values: dict[str, float]) -> dict[str, float]:
    """Average-rank percentiles on [0, 100]. Ties share the mean rank."""
    ranks = cross_sectional_ranks(values)
    return {key: rank * 100.0 for key, rank in ranks.items()}


def robust_zscore(values: dict[str, float]) -> dict[str, float]:
    if not values:
        return {}
    xs = list(values.values())
    med = float(np.median(np.asarray(xs, dtype=np.float64)))
    mad = float(np.median(np.abs(np.asarray(xs, dtype=np.float64) - med)))
    scaled = mad * 1.4826
    if scaled <= 0:
        return dict.fromkeys(values, 0.0)
    return {key: (val - med) / scaled for key, val in values.items()}


def winsorize_cs(values: dict[str, float], p: float = 0.025) -> dict[str, float]:
    if len(values) < 3:
        return dict(values)
    arr = np.asarray(list(values.values()), dtype=np.float64)
    lo, hi = np.quantile(arr, [p, 1.0 - p])
    return {key: float(min(max(val, lo), hi)) for key, val in values.items()}


def apply_cross_section(
    values: dict[str, float],
    method: NormalizationMethod,
    winsor_p: float = 0.025,
) -> dict[str, float]:
    if method is NormalizationMethod.NONE or method is NormalizationMethod.ZSCORE_TS:
        return dict(values)
    if method is NormalizationMethod.RANK:
        return cross_sectional_ranks(values)
    if method is NormalizationMethod.PERCENTILE_RANK:
        return percentile_ranks(values)
    if method is NormalizationMethod.ZSCORE_CS:
        keys = list(values.keys())
        scaled = zscore([values[k] for k in keys])
        return {keys[i]: scaled[i] for i in range(len(keys))}
    if method is NormalizationMethod.ROBUST_ZSCORE_CS:
        return robust_zscore(values)
    if method is NormalizationMethod.WINSORIZED_ZSCORE_CS:
        clipped = winsorize_cs(values, winsor_p)
        keys = list(clipped.keys())
        scaled = zscore([clipped[k] for k in keys])
        return {keys[i]: scaled[i] for i in range(len(keys))}
    raise ValueError(f"unsupported normalization: {method}")
