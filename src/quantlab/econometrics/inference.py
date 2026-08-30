"""Robust inference wrappers. Reuse Prompt 05 moving-block bootstrap and sign-flip."""

from __future__ import annotations

import numpy as np

from quantlab.domain.research import CheckResult
from quantlab.econometrics.linalg import as_vector, hac_tstat, newey_west_cov, ols_fit
from quantlab.research.statistics import moving_block_bootstrap, sign_flip_p_value


def hac_slope(y: list[float], x: list[float], *, lags: int) -> tuple[float | None, float | None]:
    if len(y) < 12 or len(y) != len(x):
        return None, None
    yy = as_vector(y)
    xx = np.column_stack([np.ones(len(y)), as_vector(x)])
    beta, resid, _ = ols_fit(yy, xx)
    cov = newey_west_cov(xx, resid, lags=lags)
    return float(beta[1]), hac_tstat(beta, cov, 1)


def block_bootstrap_mean(values: list[float], *, seed: int) -> np.ndarray:
    return moving_block_bootstrap(
        values, block_size=max(len(values) // 10, 2), n_boot=32, seed=seed
    )


def permutation_p(values: list[float], *, seed: int) -> float | None:
    return sign_flip_p_value(values, n_perm=64, seed=seed)


def interval(estimate: float | None, tstat: float | None) -> str:
    if estimate is None:
        return "NOT_TESTED"
    if tstat is None:
        return f"{estimate:.6g} ± unknown"
    return f"{estimate:.6g} (HAC t={tstat:.3g})"


def robust_status(estimate: float | None) -> CheckResult:
    return CheckResult.NOT_TESTED if estimate is None else CheckResult.PASS
