"""OLS, HAC, ACF helpers. Small samples return None rather than invented stats."""

from __future__ import annotations

import math

import numpy as np


def as_vector(values: list[float]) -> np.ndarray:
    return np.asarray(values, dtype=np.float64)


def ols_fit(y: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    fitted = x @ beta
    resid = y - fitted
    return beta, resid, fitted


def newey_west_cov(x: np.ndarray, resid: np.ndarray, *, lags: int) -> np.ndarray | None:
    n, k = x.shape
    if n <= k or lags < 0:
        return None
    xtx = x.T @ x
    try:
        xtx_inv = np.linalg.inv(xtx)
    except np.linalg.LinAlgError:
        return None
    meat = np.zeros((k, k), dtype=np.float64)
    score = x * resid[:, None]
    meat += score.T @ score
    lag_max = min(lags, n - 1)
    for lag in range(1, lag_max + 1):
        weight = 1.0 - lag / (lag_max + 1)
        gamma = score[lag:].T @ score[:-lag]
        meat += weight * (gamma + gamma.T)
    return xtx_inv @ meat @ xtx_inv


def hac_tstat(beta: np.ndarray, cov: np.ndarray | None, index: int = 0) -> float | None:
    if cov is None or index >= len(beta):
        return None
    var = float(cov[index, index])
    if var <= 0 or not math.isfinite(var):
        return None
    return float(beta[index] / math.sqrt(var))


def acf_values(series: np.ndarray, nlags: int) -> list[float]:
    if len(series) < 3 or nlags < 1:
        return []
    centered = series - series.mean()
    denom = float(np.dot(centered, centered))
    if denom <= 0:
        return []
    n = len(centered)
    out = [1.0]
    for lag in range(1, min(nlags, n - 1) + 1):
        num = float(np.dot(centered[lag:], centered[:-lag]))
        out.append(num / denom)
    return out


def pacf_values(series: np.ndarray, nlags: int) -> list[float]:
    rhos = acf_values(series, nlags)
    if len(rhos) < 2:
        return []
    pacf = [1.0]
    for k in range(1, len(rhos)):
        r = np.array(rhos[1 : k + 1], dtype=np.float64)
        toeplitz = np.array(
            [[rhos[abs(i - j)] for j in range(k)] for i in range(k)],
            dtype=np.float64,
        )
        try:
            phi = np.linalg.solve(toeplitz, r)
        except np.linalg.LinAlgError:
            pacf.append(float("nan"))
            continue
        pacf.append(float(phi[-1]))
    return pacf


def ljung_box(series: np.ndarray, nlags: int) -> float | None:
    rhos = acf_values(series, nlags)
    if len(rhos) < 2:
        return None
    n = len(series)
    total = 0.0
    for k, rho in enumerate(rhos[1:], start=1):
        total += (rho * rho) / (n - k)
    return n * (n + 2) * total


def aic_of_rss(rss: float, n: int, k: int) -> float | None:
    if n <= k or rss <= 0:
        return None
    return n * math.log(rss / n) + 2 * k
