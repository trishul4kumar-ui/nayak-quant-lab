"""Walk-forward stacking / meta-alpha. Reuses Prompt 11 linear estimators."""

from __future__ import annotations

from datetime import datetime

from quantlab.core.errors import EnsembleError, ModelError
from quantlab.ensemble.definition import EnsembleDefinition, EnsembleLeakFlags, WeightingPolicy
from quantlab.features.engine import Panel
from quantlab.learning.linear import fit_elastic, fit_ols, fit_ridge, predict_linear


def stacking_rows(
    panels: dict[str, Panel],
    labels: Panel,
    dates: list[datetime],
    names: list[str],
) -> tuple[list[list[float]], list[float]]:
    x_rows: list[list[float]] = []
    y: list[float] = []
    for as_of in dates:
        fwd = labels.get(as_of, {})
        rows = [panels.get(name, {}).get(as_of, {}) for name in names]
        keys = set(fwd)
        for row in rows:
            keys &= set(row)
        for inst in sorted(keys):
            x_rows.append([row[inst] for row in rows])
            y.append(fwd[inst])
    return x_rows, y


def fit_meta(
    definition: EnsembleDefinition,
    x_rows: list[list[float]],
    y: list[float],
) -> tuple[list[float], float]:
    if len(y) < definition.min_obs:
        raise EnsembleError("insufficient_history")
    policy = definition.weighting_policy
    try:
        if policy is WeightingPolicy.OLS_META:
            coef, intercept, _cond = fit_ols(x_rows, y)
        elif policy is WeightingPolicy.ELASTIC_STACK:
            coef, intercept, _cond = fit_elastic(x_rows, y, l1=definition.l1, l2=definition.l2)
        else:
            coef, intercept, _cond = fit_ridge(x_rows, y, definition.l2)
    except ModelError as exc:
        raise EnsembleError(str(exc)) from exc
    return coef, intercept


def predict_meta(
    rows_at_t: list[dict[str, float]],
    coef: list[float],
    intercept: float,
) -> dict[str, float]:
    if not rows_at_t:
        return {}
    keys = set(rows_at_t[0])
    for row in rows_at_t[1:]:
        keys &= set(row)
    if not keys:
        return {}
    ordered = sorted(keys)
    x_rows = [[row[inst] for row in rows_at_t] for inst in ordered]
    preds = predict_linear(x_rows, coef, intercept)
    return dict(zip(ordered, preds, strict=True))


def stack_at(
    definition: EnsembleDefinition,
    panels: dict[str, Panel],
    labels: Panel,
    train_dates: list[datetime],
    as_of: datetime,
    *,
    leaks: EnsembleLeakFlags | None = None,
) -> tuple[dict[str, float], dict[str, float]]:
    flags = leaks or EnsembleLeakFlags()
    names = definition.component_ids()
    leaky = flags.stacking_leak or flags.future_stacking or flags.full_sample_replay
    used = list(train_dates)
    if leaky:
        extra = [as_of] if as_of not in used else []
        used = used + extra
    try:
        x_rows, y = stacking_rows(panels, labels, used, names)
        coef, intercept = fit_meta(definition, x_rows, y)
    except EnsembleError:
        return {}, equal_from_coef([0.0 for _ in names], names)
    rows_at_t = [panels.get(name, {}).get(as_of, {}) for name in names]
    scores = predict_meta(rows_at_t, coef, intercept)
    return scores, coef_as_weights(coef, names)


def coef_as_weights(coef: list[float], names: list[str]) -> dict[str, float]:
    abs_vals = [abs(v) for v in coef]
    total = sum(abs_vals)
    if total <= 0:
        return equal_from_coef(coef, names)
    return {names[i]: abs_vals[i] / total for i in range(len(names))}


def equal_from_coef(_coef: list[float], names: list[str]) -> dict[str, float]:
    if not names:
        return {}
    w = 1.0 / float(len(names))
    return {name: w for name in names}
