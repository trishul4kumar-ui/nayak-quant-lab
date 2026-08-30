"""Granger predictive tests. Never labelled as proof of causation."""

from __future__ import annotations

import math

import numpy as np

from quantlab.domain.research import CheckResult
from quantlab.econometrics.enums import CausalClaim
from quantlab.econometrics.linalg import ols_fit
from quantlab.econometrics.models import CausalityTest
from quantlab.research.statistics import sign_flip_p_value


def granger_pair(
    x: list[float],
    y: list[float],
    *,
    lags: int,
    seed: int,
) -> CausalityTest:
    n = min(len(x), len(y))
    if n < 40 or lags < 1:
        return CausalityTest(
            method="granger",
            statistic=None,
            p_value=None,
            lags=lags,
            status=CheckResult.NOT_TESTED,
            note="Granger needs a longer overlap. Not causation.",
        )
    xx = np.asarray(x[-n:], dtype=np.float64)
    yy = np.asarray(y[-n:], dtype=np.float64)
    rows_r = []
    rows_u = []
    target = []
    for t in range(lags, n):
        target.append(yy[t])
        r = [1.0]
        u = [1.0]
        for lag in range(1, lags + 1):
            r.append(yy[t - lag])
            u.append(yy[t - lag])
        for lag in range(1, lags + 1):
            u.append(xx[t - lag])
        rows_r.append(r)
        rows_u.append(u)
    yv = np.asarray(target, dtype=np.float64)
    xr = np.asarray(rows_r, dtype=np.float64)
    xu = np.asarray(rows_u, dtype=np.float64)
    _, resid_r, _ = ols_fit(yv, xr)
    _, resid_u, _ = ols_fit(yv, xu)
    rss_r = float(np.sum(resid_r * resid_r))
    rss_u = float(np.sum(resid_u * resid_u))
    q = lags
    df = len(yv) - xu.shape[1]
    if df <= 0 or rss_u <= 0:
        return CausalityTest(
            method="granger",
            statistic=None,
            p_value=None,
            lags=lags,
            status=CheckResult.NOT_TESTED,
            note="Restricted/unrestricted Granger comparison is underidentified.",
        )
    stat = ((rss_r - rss_u) / q) / (rss_u / df)
    p_value = sign_flip_p_value(resid_u.tolist(), n_perm=64, seed=seed)
    return CausalityTest(
        method="granger",
        statistic=float(stat) if math.isfinite(stat) else None,
        p_value=p_value,
        lags=lags,
        claim=CausalClaim.PREDICTIVE,
        status=CheckResult.PASS if math.isfinite(stat) else CheckResult.NOT_TESTED,
        note="PREDICTIVE only. Granger is not structural causation. CORRELATION ≠ CAUSATION.",
    )
