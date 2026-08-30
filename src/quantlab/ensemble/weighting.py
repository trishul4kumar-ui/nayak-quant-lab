"""PIT ensemble weights. Hard constraints are not silently relaxed."""

from __future__ import annotations

from datetime import datetime

import numpy as np

from quantlab.adaptive.ewma import ewma_mean
from quantlab.core.errors import EnsembleError, InfeasibleEnsemble
from quantlab.ensemble.definition import EnsembleDefinition, EnsembleLeakFlags, WeightingPolicy
from quantlab.features.engine import Panel
from quantlab.research.cross_section import spearman_ic


def component_ic_history(
    panels: dict[str, Panel],
    labels: Panel,
    dates: list[datetime],
    component_id: str,
) -> list[float]:
    series: list[float] = []
    panel = panels.get(component_id, {})
    for as_of in dates:
        ic = spearman_ic(panel.get(as_of, {}), labels.get(as_of, {}))
        if ic is not None:
            series.append(ic)
    return series


def ic_matrix(
    panels: dict[str, Panel],
    labels: Panel,
    dates: list[datetime],
    names: list[str],
) -> np.ndarray:
    rows: list[list[float]] = []
    for as_of in dates:
        row: list[float] = []
        ok = True
        fwd = labels.get(as_of, {})
        for name in names:
            ic = spearman_ic(panels.get(name, {}).get(as_of, {}), fwd)
            if ic is None:
                ok = False
                break
            row.append(ic)
        if ok:
            rows.append(row)
    if not rows:
        return np.zeros((0, len(names)), dtype=np.float64)
    return np.asarray(rows, dtype=np.float64)


def shrink_sample_covariance(arr: np.ndarray, shrinkage: float) -> np.ndarray:
    """Same diagonal-shrinkage formula as Prompt 08 estimator='shrinkage'."""
    if arr.shape[0] < 2:
        raise EnsembleError("insufficient_history")
    sample = np.cov(arr, rowvar=False, ddof=0)
    if sample.ndim == 0:
        sample = np.array([[float(sample)]], dtype=np.float64)
    intensity = min(max(float(shrinkage), 0.0), 1.0)
    target = np.diag(np.diag(sample))
    cov = (1.0 - intensity) * sample + intensity * target
    return 0.5 * (cov + cov.T)


def constrain_weights(
    weights: dict[str, float],
    definition: EnsembleDefinition,
    *,
    previous: dict[str, float] | None = None,
) -> tuple[dict[str, float], bool]:
    names = [item.component_id for item in definition.components if item.component_id in weights]
    if not names:
        raise InfeasibleEnsemble("no component weights")
    n = len(names)
    if definition.min_weight * n > 1.0 + 1e-12:
        raise InfeasibleEnsemble("min_weight * n_components > 1")
    raw = [max(float(weights[name]), 0.0) for name in names]
    total = sum(raw)
    fallback = False
    if total <= 0:
        raw = [1.0 for _ in names]
        total = float(n)
        fallback = True
    clipped = [
        min(max(value / total, definition.min_weight), definition.max_weight) for value in raw
    ]
    clipped_total = sum(clipped)
    if clipped_total <= 0:
        raise InfeasibleEnsemble("weights vanished after clipping")
    out = [value / clipped_total for value in clipped]
    if any(value > definition.max_weight + 1e-9 for value in out):
        raise InfeasibleEnsemble("max_weight infeasible after renormalization")
    hhi = sum(value * value for value in out)
    if hhi > definition.max_concentration + 1e-12:
        raise InfeasibleEnsemble("max_concentration")
    mapped = dict(zip(names, out, strict=True))
    if definition.max_turnover is not None and previous is not None:
        turnover = 0.5 * sum(abs(mapped.get(n, 0.0) - previous.get(n, 0.0)) for n in names)
        if turnover > definition.max_turnover + 1e-12:
            raise InfeasibleEnsemble("max_turnover")
    return mapped, fallback


def equal_weights(names: list[str]) -> dict[str, float]:
    if not names:
        raise EnsembleError("empty_components")
    w = 1.0 / float(len(names))
    return {name: w for name in names}


def weight_turnover(current: dict[str, float], previous: dict[str, float] | None) -> float | None:
    if previous is None:
        return None
    keys = set(current) | set(previous)
    return 0.5 * sum(abs(current.get(k, 0.0) - previous.get(k, 0.0)) for k in keys)


def compute_weights(
    definition: EnsembleDefinition,
    panels: dict[str, Panel],
    labels: Panel,
    hist_dates: list[datetime],
    *,
    previous: dict[str, float] | None = None,
    leaks: EnsembleLeakFlags | None = None,
) -> tuple[dict[str, float], bool]:
    flags = leaks or EnsembleLeakFlags()
    names = definition.component_ids()
    policy = definition.weighting_policy
    if policy in {WeightingPolicy.EQUAL, WeightingPolicy.RANK_SUM}:
        return equal_weights(names), False
    if policy in {
        WeightingPolicy.RIDGE_STACK,
        WeightingPolicy.ELASTIC_STACK,
        WeightingPolicy.OLS_META,
    }:
        return equal_weights(names), False

    series = {name: component_ic_history(panels, labels, hist_dates, name) for name in names}
    min_obs = definition.min_obs
    if all(len(series[name]) < min_obs for name in names):
        return equal_weights(names), True

    raw: dict[str, float] = {}
    if policy is WeightingPolicy.STATIC_IC:
        for name in names:
            hist = series[name]
            raw[name] = 0.0 if len(hist) < min_obs else max(sum(hist) / len(hist), 0.0)
    elif policy is WeightingPolicy.ROLLING_IC:
        window = definition.training_window
        for name in names:
            hist = series[name][-window:]
            raw[name] = 0.0 if len(hist) < min_obs else max(sum(hist) / len(hist), 0.0)
    elif policy is WeightingPolicy.EWMA_IC:
        half = definition.half_life or 10.0
        for name in names:
            hist = series[name]
            mean = ewma_mean(hist, half) if len(hist) >= min_obs else None
            raw[name] = 0.0 if mean is None else max(mean, 0.0)
    elif policy is WeightingPolicy.INVERSE_VOL:
        for name in names:
            hist = series[name]
            if len(hist) < min_obs:
                raw[name] = 0.0
                continue
            std = float(np.std(np.asarray(hist, dtype=np.float64), ddof=0))
            raw[name] = 0.0 if std <= 1e-12 else 1.0 / std
    elif policy is WeightingPolicy.BAYESIAN_HIT:
        for name in names:
            hist = series[name]
            if len(hist) < min_obs:
                raw[name] = 0.0
                continue
            a = 1.0 + sum(1.0 for v in hist if v > 0)
            b = 1.0 + sum(1.0 for v in hist if v <= 0)
            raw[name] = a / (a + b)
    elif policy in {WeightingPolicy.CORRELATION_AWARE, WeightingPolicy.REGULARIZED}:
        raw = _corr_or_regularized(definition, panels, labels, hist_dates, names, previous, flags)
    else:
        raise EnsembleError(f"unknown weighting policy {policy}")
    return constrain_weights(raw, definition, previous=previous)


def _corr_or_regularized(
    definition: EnsembleDefinition,
    panels: dict[str, Panel],
    labels: Panel,
    hist_dates: list[datetime],
    names: list[str],
    previous: dict[str, float] | None,
    flags: EnsembleLeakFlags,
) -> dict[str, float]:
    arr = ic_matrix(panels, labels, hist_dates, names)
    if arr.shape[0] < max(definition.min_obs, 2):
        return equal_weights(names)
    mu = np.clip(arr.mean(axis=0), 0.0, None)
    try:
        cov = shrink_sample_covariance(arr, definition.shrinkage)
    except EnsembleError:
        return equal_weights(names)
    if flags.future_covariance:
        cov = shrink_sample_covariance(arr, definition.shrinkage)
    gamma = definition.weight_stability_penalty if previous else 0.0
    eye = np.eye(len(names), dtype=np.float64)
    rhs = definition.risk_aversion * mu
    lhs = cov + gamma * eye
    if previous is not None and gamma > 0:
        prev = np.array([previous.get(name, 0.0) for name in names], dtype=np.float64)
        rhs = rhs + gamma * prev
    try:
        solved = np.linalg.solve(lhs, rhs)
    except np.linalg.LinAlgError as exc:
        raise EnsembleError("singular_weight_problem") from exc
    raw = {name: max(float(solved[i]), 0.0) for i, name in enumerate(names)}
    if sum(raw.values()) <= 0:
        return equal_weights(names)
    return raw
