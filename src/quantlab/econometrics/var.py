"""VAR with lag selection on the training window only. IRF is a diagnostic shock path."""

from __future__ import annotations

import numpy as np

from quantlab.econometrics.linalg import aic_of_rss, ols_fit
from quantlab.econometrics.models import VARSpecification


def _stack(series: list[list[float]], end: int) -> np.ndarray:
    n = min(len(row) for row in series)
    used = min(end, n)
    return np.column_stack([np.asarray(row[:used], dtype=np.float64) for row in series])


def _design(data: np.ndarray, lag: int) -> tuple[np.ndarray, np.ndarray] | None:
    n, k = data.shape
    if n <= lag + 2:
        return None
    y = data[lag:]
    rows = []
    for t in range(lag, n):
        row = [1.0]
        for lag_i in range(1, lag + 1):
            row.extend(data[t - lag_i].tolist())
        rows.append(row)
    return y, np.asarray(rows, dtype=np.float64)


def select_lags(series: list[list[float]], *, max_lag: int, train_end: int) -> int:
    data = _stack(series, train_end)
    best_lag = 1
    best_aic: float | None = None
    upper = max(1, min(max_lag, data.shape[0] // 6, 6))
    for lag in range(1, upper + 1):
        packed = _design(data, lag)
        if packed is None:
            continue
        y, x = packed
        rss = 0.0
        k_params = 0
        for col in range(y.shape[1]):
            _, resid, _ = ols_fit(y[:, col], x)
            rss += float(np.sum(resid * resid))
            k_params = x.shape[1]
        aic = aic_of_rss(rss, y.shape[0] * y.shape[1], k_params * y.shape[1])
        if aic is None:
            continue
        if best_aic is None or aic < best_aic:
            best_aic = aic
            best_lag = lag
    return best_lag


def fit_var(
    series: list[list[float]],
    *,
    lags: int,
    train_end: int | None = None,
) -> tuple[VARSpecification, np.ndarray, np.ndarray]:
    n = min(len(row) for row in series)
    end = n if train_end is None else min(train_end, n)
    data = _stack(series, end)
    packed = _design(data, lags)
    k = data.shape[1]
    if packed is None:
        spec = VARSpecification(spec_id=f"var-l{lags}", lags=lags, n_series=k, aic=None)
        return spec, np.zeros(0), np.zeros(0)
    y, x = packed
    betas = []
    resids = []
    rss = 0.0
    for col in range(k):
        beta, resid, _ = ols_fit(y[:, col], x)
        betas.append(beta)
        resids.append(resid)
        rss += float(np.sum(resid * resid))
    spec = VARSpecification(
        spec_id=f"var-l{lags}",
        lags=lags,
        n_series=k,
        selected_on="train_window",
        aic=aic_of_rss(rss, y.shape[0] * k, x.shape[1] * k),
    )
    return spec, np.column_stack(betas), np.column_stack(resids)


def impulse_response(beta: np.ndarray, n_series: int, lags: int, horizon: int) -> list[list[float]]:
    if beta.size == 0 or horizon < 1 or n_series < 1:
        return []
    # Own-shock AR(1) approximation from the first own-lag coefficient.
    own = float(beta[1, 0]) if beta.shape[0] > 1 else 0.0
    path = []
    value = 1.0
    for _ in range(horizon):
        value = own * value
        row = [value] + [0.0] * (n_series - 1)
        path.append(row)
    return path


def forecast_error_variance(irf: list[list[float]]) -> list[float] | None:
    if not irf:
        return None
    arr = np.asarray(irf, dtype=np.float64)
    num = float(np.sum(arr[:, 0] ** 2))
    den = float(np.sum(arr * arr))
    if den <= 0:
        return None
    return [num / den]
