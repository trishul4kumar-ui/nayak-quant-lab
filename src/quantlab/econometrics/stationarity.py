"""ADF and KPSS on the estimation window only. PP stays an explicit NOT_TESTED interface."""

from __future__ import annotations

import numpy as np

from quantlab.domain.research import CheckResult
from quantlab.econometrics.linalg import as_vector, ols_fit
from quantlab.econometrics.models import StationarityTest

# MacKinnon (1991) large-sample critical values, constant, no trend.
_ADF_CRIT_5 = -2.86
_KPSS_CRIT_5 = 0.463


def _lags_for(n: int, requested: int) -> int:
    if n < 20:
        return 0
    return max(0, min(requested, n // 10, 8))


def adf_test(values: list[float], *, lags: int | None = None) -> StationarityTest:
    series = as_vector(values)
    n = len(series)
    if n < 20:
        return StationarityTest(
            method="adf",
            statistic=None,
            critical_5=_ADF_CRIT_5,
            rejects_unit_root=None,
            lags=0,
            n=n,
            status=CheckResult.NOT_TESTED,
            note="ADF needs a longer window. Small sample is NOT_TESTED, not a unit-root claim.",
        )
    used_lags = _lags_for(n, 1 if lags is None else lags)
    dy = np.diff(series)
    y_lag = series[:-1]
    start = used_lags
    y = dy[start:]
    cols = [np.ones(len(y)), y_lag[start:]]
    for lag in range(1, used_lags + 1):
        cols.append(dy[start - lag : len(dy) - lag])
    x = np.column_stack(cols)
    beta, *_ = ols_fit(y, x)
    rss = float(np.sum((y - x @ beta) ** 2))
    sigma2 = rss / max(len(y) - x.shape[1], 1)
    xtx_inv = np.linalg.pinv(x.T @ x)
    se = float(np.sqrt(max(sigma2 * xtx_inv[1, 1], 0.0)))
    stat = None if se == 0 else float(beta[1] / se)
    rejects = None if stat is None else stat < _ADF_CRIT_5
    return StationarityTest(
        method="adf",
        statistic=stat,
        critical_5=_ADF_CRIT_5,
        rejects_unit_root=rejects,
        lags=used_lags,
        n=n,
        status=CheckResult.PASS if stat is not None else CheckResult.NOT_TESTED,
        note="Tabulated MacKinnon 5% critical value. Not a certified p-value.",
    )


def kpss_test(values: list[float]) -> StationarityTest:
    series = as_vector(values)
    n = len(series)
    if n < 20:
        return StationarityTest(
            method="kpss",
            statistic=None,
            critical_5=_KPSS_CRIT_5,
            rejects_unit_root=None,
            lags=0,
            n=n,
            status=CheckResult.NOT_TESTED,
            note="KPSS needs a longer window.",
        )
    resid = series - series.mean()
    s = np.cumsum(resid)
    lags = max(int(np.sqrt(n)), 1)
    gamma0 = float(np.dot(resid, resid) / n)
    omega = gamma0
    for lag in range(1, lags + 1):
        w = 1.0 - lag / (lags + 1)
        omega += 2 * w * float(np.dot(resid[lag:], resid[:-lag]) / n)
    if omega <= 0:
        return StationarityTest(
            method="kpss",
            statistic=None,
            critical_5=_KPSS_CRIT_5,
            rejects_unit_root=None,
            lags=lags,
            n=n,
            status=CheckResult.NOT_TESTED,
            note="KPSS long-run variance is non-positive.",
        )
    stat = float(np.dot(s, s) / (n * n * omega))
    # KPSS null is stationarity; large statistic rejects stationarity (unit-root-like).
    rejects_stationarity = stat > _KPSS_CRIT_5
    return StationarityTest(
        method="kpss",
        statistic=stat,
        critical_5=_KPSS_CRIT_5,
        rejects_unit_root=rejects_stationarity,
        lags=lags,
        n=n,
        status=CheckResult.PASS,
        note="KPSS null is stationarity. rejects_unit_root here means reject stationarity.",
    )


def phillips_perron_interface(values: list[float]) -> StationarityTest:
    return StationarityTest(
        method="phillips_perron",
        statistic=None,
        critical_5=None,
        rejects_unit_root=None,
        lags=0,
        n=len(values),
        status=CheckResult.NOT_TESTED,
        note="Phillips-Perron is an interface only until a certified implementation is sourced.",
    )


def difference(values: list[float]) -> list[float]:
    series = as_vector(values)
    if len(series) < 2:
        return []
    return [float(value) for value in np.diff(series)]
