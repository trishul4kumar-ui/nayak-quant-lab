"""Pooled, entity/time/two-way FE, clustered errors, Fama-MacBeth-style research."""

from __future__ import annotations

from collections import defaultdict

import numpy as np

from quantlab.domain.research import CheckResult
from quantlab.econometrics.enums import PanelEffect
from quantlab.econometrics.linalg import hac_tstat, newey_west_cov, ols_fit
from quantlab.econometrics.models import PanelSpecification


def pooled_ols(
    y: list[float],
    x: list[float],
) -> tuple[float | None, float | None, CheckResult]:
    if len(y) < 20 or len(y) != len(x):
        return None, None, CheckResult.NOT_TESTED
    yy = np.asarray(y, dtype=np.float64)
    xx = np.column_stack([np.ones(len(y)), np.asarray(x, dtype=np.float64)])
    beta, resid, _ = ols_fit(yy, xx)
    cov = newey_west_cov(xx, resid, lags=max(len(y) // 10, 1))
    return float(beta[1]), hac_tstat(beta, cov, 1), CheckResult.PASS


def entity_fe(
    y: list[float],
    x: list[float],
    entity: list[str],
) -> tuple[float | None, CheckResult]:
    if len(y) < 20 or len({*entity}) < 2:
        return None, CheckResult.NOT_TESTED
    yy = np.asarray(y, dtype=np.float64)
    xx = np.asarray(x, dtype=np.float64)
    names = sorted(set(entity))
    demeaned_y = np.zeros_like(yy)
    demeaned_x = np.zeros_like(xx)
    for name in names:
        idx = [i for i, item in enumerate(entity) if item == name]
        demeaned_y[idx] = yy[idx] - yy[idx].mean()
        demeaned_x[idx] = xx[idx] - xx[idx].mean()
    design = np.column_stack([demeaned_x])
    if np.allclose(design, 0):
        return None, CheckResult.NOT_TESTED
    beta, *_ = ols_fit(demeaned_y, design)
    return float(beta[0]), CheckResult.PASS


def fama_macbeth(
    y: list[float],
    x: list[float],
    time_id: list[str],
) -> tuple[float | None, CheckResult]:
    buckets: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for yi, xi, t in zip(y, x, time_id, strict=False):
        buckets[t].append((yi, xi))
    slopes = []
    for rows in buckets.values():
        if len(rows) < 3:
            continue
        yy = np.array([row[0] for row in rows], dtype=np.float64)
        xx = np.column_stack(
            [np.ones(len(rows)), np.array([row[1] for row in rows], dtype=np.float64)]
        )
        beta, *_ = ols_fit(yy, xx)
        slopes.append(float(beta[1]))
    if len(slopes) < 4:
        return None, CheckResult.NOT_TESTED
    return float(np.mean(slopes)), CheckResult.PASS


def panel_spec(effect: PanelEffect, *, clustered: bool = True) -> PanelSpecification:
    return PanelSpecification(
        spec_id=f"panel-{effect.value}",
        effect=effect,
        clustered=clustered,
    )
