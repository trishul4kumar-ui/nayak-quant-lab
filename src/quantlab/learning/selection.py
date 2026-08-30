"""Train-window feature selection. Full-sample selection is not predictive."""

from __future__ import annotations

import math

from quantlab.core.errors import ModelError
from quantlab.learning.definition import SelectionMethod
from quantlab.learning.linear import fit_lasso
from quantlab.research.cross_section import spearman_ic


def select_features(
    x_rows: list[list[float]],
    y: list[float],
    names: list[str],
    method: SelectionMethod,
    k: int,
    l1: float = 0.01,
) -> list[str]:
    if method is SelectionMethod.NONE:
        return list(names)
    if len(names) != (0 if not x_rows else len(x_rows[0])):
        raise ModelError("feature schema mismatch")
    if method is SelectionMethod.UNIVARIATE_IC:
        scored: list[tuple[float, str]] = []
        for j, name in enumerate(names):
            feat = {str(i): x_rows[i][j] for i in range(len(x_rows))}
            lab = {str(i): y[i] for i in range(len(y))}
            ic = spearman_ic(feat, lab)
            scored.append((abs(0.0 if ic is None else ic), name))
        scored.sort(key=lambda item: item[0], reverse=True)
        chosen = [name for _ic, name in scored[: max(k, 1)]]
        if not chosen:
            raise ModelError("feature selection produced an empty set")
        return chosen
    if method is SelectionMethod.CORRELATION_FILTER:
        keep: list[str] = []
        for j, name in enumerate(names):
            redundant = False
            for kept in keep:
                kj = names.index(kept)
                corr = _pearson_col([row[j] for row in x_rows], [row[kj] for row in x_rows])
                if corr is not None and abs(corr) > 0.95:
                    redundant = True
                    break
            if not redundant:
                keep.append(name)
            if len(keep) >= k:
                break
        return keep or list(names[:1])
    coef, _intercept, _cond = fit_lasso(x_rows, y, l1)
    nonzero = [names[j] for j, value in enumerate(coef) if abs(value) > 1e-12]
    return nonzero[:k] if nonzero else list(names[:1])


def project(x_rows: list[list[float]], names: list[str], selected: list[str]) -> list[list[float]]:
    idx = [names.index(name) for name in selected]
    return [[row[j] for j in idx] for row in x_rows]


def _pearson_col(a: list[float], b: list[float]) -> float | None:
    n = len(a)
    if n < 3:
        return None
    ma = sum(a) / n
    mb = sum(b) / n
    num = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    da = sum((v - ma) ** 2 for v in a)
    db = sum((v - mb) ** 2 for v in b)
    if da <= 0 or db <= 0:
        return None
    denom = math.sqrt(da) * math.sqrt(db)
    return float(num / denom)
