"""Block bootstrap, sign-flip permutation, and effect-size reporting.

Time-series dependence is respected by default (moving-block bootstrap).
IID shuffling of returns is not offered as a research-grade null.
"""

from __future__ import annotations

from statistics import NormalDist

import numpy as np
from pydantic import BaseModel

from quantlab.domain.research import CheckResult


class StatisticalReport(BaseModel):
    schema_version: str = "1"
    n: int
    mean: float
    std: float
    effect_size: float | None
    mean_ci_low: float | None
    mean_ci_high: float | None
    p_value: float | None
    null_model: str
    method: str
    seed: int
    status: CheckResult
    lag1_autocorrelation: float | None = None
    heteroskedasticity: CheckResult = CheckResult.NOT_TESTED
    note: str = ""


def _as_array(returns: list[float]) -> np.ndarray:
    return np.asarray(returns, dtype=np.float64)


def moving_block_bootstrap(
    returns: list[float],
    *,
    block_size: int,
    n_boot: int,
    seed: int,
) -> np.ndarray:
    arr = _as_array(returns)
    n = len(arr)
    if n < 2 or block_size < 1:
        return np.empty((0, 0))
    block = min(block_size, n)
    n_blocks = int(np.ceil(n / block))
    rng = np.random.default_rng(seed)
    out = np.empty((n_boot, n), dtype=np.float64)
    max_start = n - block + 1
    for i in range(n_boot):
        starts = rng.integers(0, max_start, size=n_blocks)
        sample = np.concatenate([arr[int(s) : int(s) + block] for s in starts])[:n]
        out[i] = sample
    return out


def sign_flip_p_value(returns: list[float], *, n_perm: int, seed: int) -> float | None:
    """Two-sided p-value for mean return under a sign-flip null (no directional edge)."""
    arr = _as_array(returns)
    if len(arr) < 2:
        return None
    observed = float(abs(arr.mean()))
    rng = np.random.default_rng(seed)
    count = 0
    for _ in range(n_perm):
        signs = rng.choice(np.array([-1.0, 1.0]), size=len(arr))
        if abs(float((arr * signs).mean())) >= observed:
            count += 1
    return (count + 1) / (n_perm + 1)


def evaluate_returns(
    returns: list[float],
    *,
    seed: int = 0,
    n_boot: int = 200,
    block_size: int = 5,
    n_perm: int = 200,
) -> StatisticalReport:
    arr = _as_array(returns)
    n = len(arr)
    if n < 8:
        return StatisticalReport(
            n=n,
            mean=0.0 if n == 0 else float(arr.mean()),
            std=0.0 if n < 2 else float(arr.std(ddof=0)),
            effect_size=None,
            mean_ci_low=None,
            mean_ci_high=None,
            p_value=None,
            null_model="sign_flip_mean",
            method="insufficient_sample",
            seed=seed,
            status=CheckResult.NOT_TESTED,
            lag1_autocorrelation=None,
            heteroskedasticity=CheckResult.NOT_TESTED,
            note="need at least 8 periodic returns for bootstrap/CI",
        )
    mean = float(arr.mean())
    std = float(arr.std(ddof=0))
    effect = None if std == 0.0 else float(mean / std)
    boot = moving_block_bootstrap(returns, block_size=block_size, n_boot=n_boot, seed=seed)
    means = boot.mean(axis=1)
    lo, hi = float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))
    p_value = sign_flip_p_value(returns, n_perm=n_perm, seed=seed)
    lag1: float | None = None
    if float(arr.std()) == 0.0:
        lag1 = 0.0
    else:
        corr = float(np.corrcoef(arr[:-1], arr[1:])[0, 1])
        lag1 = corr if np.isfinite(corr) else None
    return StatisticalReport(
        n=n,
        mean=mean,
        std=std,
        effect_size=effect,
        mean_ci_low=lo,
        mean_ci_high=hi,
        p_value=p_value,
        null_model="sign_flip_mean",
        method="moving_block_bootstrap_plus_sign_flip",
        seed=seed,
        status=CheckResult.PASS,
        lag1_autocorrelation=lag1,
        heteroskedasticity=CheckResult.NOT_TESTED,
        note=(
            "p-value is not a promotion criterion; economic significance is separate. "
            "heteroskedasticity-robust inference is NOT_TESTED (no regression in this phase)"
        ),
    )


def normal_ppf(p: float) -> float:
    return float(NormalDist().inv_cdf(p))
