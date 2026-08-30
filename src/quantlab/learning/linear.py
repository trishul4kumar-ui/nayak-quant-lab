"""Linear and robust estimators. OLS is not causal inference."""

from __future__ import annotations

import math

import numpy as np

from quantlab.core.errors import ModelError


def fit_ols(x_rows: list[list[float]], y: list[float]) -> tuple[list[float], float, float]:
    x = np.asarray(x_rows, dtype=np.float64)
    target = np.asarray(y, dtype=np.float64)
    _check_finite(x, target)
    design = _with_intercept(x)
    cond = _condition(design)
    try:
        beta, _, rank, _ = np.linalg.lstsq(design, target, rcond=None)
    except np.linalg.LinAlgError as exc:
        raise ModelError("singular_matrix") from exc
    if int(rank) < design.shape[1]:
        raise ModelError("singular_matrix")
    return [float(v) for v in beta[1:]], float(beta[0]), cond


def fit_ridge(
    x_rows: list[list[float]], y: list[float], l2: float
) -> tuple[list[float], float, float]:
    x = np.asarray(x_rows, dtype=np.float64)
    target = np.asarray(y, dtype=np.float64)
    _check_finite(x, target)
    x_mean = x.mean(axis=0)
    y_mean = float(target.mean())
    xc = x - x_mean
    yc = target - y_mean
    xtx = xc.T @ xc + float(l2) * np.eye(xc.shape[1])
    cond = _condition(xtx)
    try:
        coef = np.linalg.solve(xtx, xc.T @ yc)
    except np.linalg.LinAlgError as exc:
        raise ModelError("singular_matrix") from exc
    intercept = y_mean - float(x_mean @ coef)
    return [float(v) for v in coef], intercept, cond


def fit_elastic(
    x_rows: list[list[float]],
    y: list[float],
    *,
    l1: float,
    l2: float,
    n_iter: int = 400,
) -> tuple[list[float], float, float]:
    x = np.asarray(x_rows, dtype=np.float64)
    target = np.asarray(y, dtype=np.float64)
    _check_finite(x, target)
    n, p = x.shape
    x_mean = x.mean(axis=0)
    y_mean = float(target.mean())
    xc = x - x_mean
    yc = target - y_mean
    col_ss = np.sum(xc * xc, axis=0)
    if np.any(col_ss <= 0):
        raise ModelError("constant_feature")
    beta = np.zeros(p, dtype=np.float64)
    for _ in range(n_iter):
        prev = beta.copy()
        for j in range(p):
            residual = yc - xc @ beta + xc[:, j] * beta[j]
            rho = float(xc[:, j] @ residual)
            beta[j] = _soft(rho, n * float(l1)) / (float(col_ss[j]) + n * float(l2))
        if float(np.max(np.abs(beta - prev))) < 1e-8:
            break
    intercept = y_mean - float(x_mean @ beta)
    cond = _condition(xc.T @ xc + float(l2) * np.eye(p))
    return [float(v) for v in beta], intercept, cond


def fit_lasso(
    x_rows: list[list[float]], y: list[float], l1: float
) -> tuple[list[float], float, float]:
    return fit_elastic(x_rows, y, l1=l1, l2=0.0)


def fit_huber(
    x_rows: list[list[float]],
    y: list[float],
    delta: float,
    n_iter: int = 50,
) -> tuple[list[float], float, float]:
    x = np.asarray(x_rows, dtype=np.float64)
    target = np.asarray(y, dtype=np.float64)
    _check_finite(x, target)
    design = _with_intercept(x)
    beta = np.linalg.lstsq(design, target, rcond=None)[0]
    for _ in range(n_iter):
        resid = target - design @ beta
        weights = np.ones_like(resid)
        large = np.abs(resid) > float(delta)
        weights[large] = float(delta) / np.abs(resid[large])
        wsqrt = np.sqrt(weights)
        try:
            beta = np.linalg.lstsq(design * wsqrt[:, None], target * wsqrt, rcond=None)[0]
        except np.linalg.LinAlgError as exc:
            raise ModelError("unstable_fit") from exc
    cond = _condition(design)
    return [float(v) for v in beta[1:]], float(beta[0]), cond


def predict_linear(x_rows: list[list[float]], coef: list[float], intercept: float) -> list[float]:
    x = np.asarray(x_rows, dtype=np.float64)
    beta = np.asarray(coef, dtype=np.float64)
    return [float(v) for v in (x @ beta + intercept).tolist()]


def rmse(predicted: list[float], actual: list[float]) -> float | None:
    if not predicted or len(predicted) != len(actual):
        return None
    err = [(predicted[i] - actual[i]) ** 2 for i in range(len(predicted))]
    return math.sqrt(sum(err) / len(err))


def _with_intercept(x: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones(x.shape[0]), x])


def _condition(matrix: np.ndarray) -> float:
    s = np.linalg.svd(matrix, compute_uv=False)
    tiny = float(s[-1])
    if tiny <= 0 or not math.isfinite(tiny):
        return float("inf")
    return float(s[0] / tiny)


def _soft(value: float, thresh: float) -> float:
    if value > thresh:
        return value - thresh
    if value < -thresh:
        return value + thresh
    return 0.0


def _check_finite(x: np.ndarray, y: np.ndarray) -> None:
    if x.size == 0 or y.size == 0:
        raise ModelError("insufficient_history")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ModelError("non_finite_values")
    if float(np.std(y)) == 0.0:
        raise ModelError("constant_target")
