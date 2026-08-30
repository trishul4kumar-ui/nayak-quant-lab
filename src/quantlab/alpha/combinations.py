"""Explicit alpha combinations. No test-set weight search."""

from __future__ import annotations

from quantlab.features.engine import Panel
from quantlab.math.metrics import cross_sectional_ranks, zscore


def zscore_map(values: dict[str, float]) -> dict[str, float]:
    keys = list(values.keys())
    scaled = zscore([values[k] for k in keys])
    return {keys[i]: scaled[i] for i in range(len(keys))}


def equal_weight_zscore(rows: list[dict[str, float]]) -> dict[str, float]:
    if not rows:
        return {}
    keys = set(rows[0])
    for row in rows[1:]:
        keys &= set(row)
    combined: dict[str, float] = {}
    scaled_rows = [zscore_map({k: row[k] for k in keys}) for row in rows]
    n = float(len(scaled_rows))
    for key in keys:
        combined[key] = sum(row[key] for row in scaled_rows) / n
    return combined


def weighted_zscore(rows: list[dict[str, float]], weights: list[float]) -> dict[str, float]:
    if len(rows) != len(weights):
        raise ValueError("weights must match the number of inputs")
    total = sum(weights)
    if total == 0:
        raise ValueError("weights must not sum to zero")
    keys = set(rows[0])
    for row in rows[1:]:
        keys &= set(row)
    scaled_rows = [zscore_map({k: row[k] for k in keys}) for row in rows]
    combined: dict[str, float] = {}
    for key in keys:
        combined[key] = sum(weights[i] * scaled_rows[i][key] for i in range(len(rows))) / total
    return combined


def rank_average(rows: list[dict[str, float]]) -> dict[str, float]:
    if not rows:
        return {}
    keys = set(rows[0])
    for row in rows[1:]:
        keys &= set(row)
    ranks = [cross_sectional_ranks({k: row[k] for k in keys}) for row in rows]
    n = float(len(ranks))
    return {key: sum(row[key] for row in ranks) / n for key in keys}


def rank_sum(rows: list[dict[str, float]]) -> dict[str, float]:
    if not rows:
        return {}
    keys = set(rows[0])
    for row in rows[1:]:
        keys &= set(row)
    ranks = [cross_sectional_ranks({k: row[k] for k in keys}) for row in rows]
    return {key: sum(row[key] for row in ranks) for key in keys}


def linear_combo(rows: list[dict[str, float]], weights: list[float]) -> dict[str, float]:
    if len(rows) != len(weights):
        raise ValueError("weights must match the number of inputs")
    keys = set(rows[0])
    for row in rows[1:]:
        keys &= set(row)
    return {key: sum(weights[i] * rows[i][key] for i in range(len(rows))) for key in keys}


def residualize(y: dict[str, float], x: dict[str, float]) -> dict[str, float] | None:
    """Contemporaneous cross-sectional OLS residual of y on x plus intercept."""
    keys = [k for k in y if k in x]
    n = len(keys)
    if n < 3:
        return None
    xs = [x[k] for k in keys]
    ys = [y[k] for k in keys]
    mx = sum(xs) / n
    my = sum(ys) / n
    varx = sum((v - mx) ** 2 for v in xs)
    if varx <= 0:
        return None
    cov = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    beta = cov / varx
    intercept = my - beta * mx
    return {keys[i]: ys[i] - (intercept + beta * xs[i]) for i in range(n)}


def combine_panels(panels: list[Panel], combiner: str, weights: list[float] | None = None) -> Panel:
    dates = set(panels[0])
    for panel in panels[1:]:
        dates &= set(panel)
    out: Panel = {}
    for as_of in sorted(dates):
        rows = [panel[as_of] for panel in panels]
        if combiner == "equal_weight_zscore":
            out[as_of] = equal_weight_zscore(rows)
        elif combiner == "weighted_zscore":
            out[as_of] = weighted_zscore(rows, weights or [1.0] * len(rows))
        elif combiner == "rank_average":
            out[as_of] = rank_average(rows)
        elif combiner == "rank_sum":
            out[as_of] = rank_sum(rows)
        elif combiner == "linear":
            out[as_of] = linear_combo(rows, weights or [1.0] * len(rows))
        elif combiner == "zscore_sub" and len(rows) == 2:
            out[as_of] = linear_combo([zscore_map(rows[0]), zscore_map(rows[1])], [1.0, -1.0])
        elif combiner in {"rank", "zscore"} and len(rows) == 1:
            out[as_of] = (
                cross_sectional_ranks(rows[0]) if combiner == "rank" else zscore_map(rows[0])
            )
        else:
            raise ValueError(f"unsupported combiner {combiner} for {len(rows)} inputs")
    return out
