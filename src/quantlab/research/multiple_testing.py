"""Multiple-testing corrections and deflated-Sharpe / PBO architecture.

A strategy found after many trials is not equivalent to a pre-registered test.
"""

from __future__ import annotations

import math
from enum import StrEnum

from pydantic import BaseModel, Field

from quantlab.domain.research import CheckResult
from quantlab.research.statistics import normal_ppf


class CorrectionMethod(StrEnum):
    BENJAMINI_HOCHBERG = "benjamini_hochberg"
    BONFERRONI = "bonferroni"
    HOLM = "holm"


class HypothesisRecord(BaseModel):
    hypothesis_id: str
    family_id: str
    p_value: float | None = None
    selected: bool = False
    parent_experiment_id: str = ""


class MultipleTestingReport(BaseModel):
    schema_version: str = "1"
    n_hypotheses: int
    method: CorrectionMethod | None = None
    alpha: float = 0.05
    adjusted: list[float] = Field(default_factory=list)
    discoveries: int = 0
    status: CheckResult
    note: str = ""


class DeflatedSharpeReport(BaseModel):
    schema_version: str = "1"
    naive_sharpe: float
    deflated_sharpe: float | None
    n_trials: int
    n_periods: int
    status: CheckResult
    note: str = ""


class OverfittingReport(BaseModel):
    schema_version: str = "1"
    n_trials: int
    selection: str
    pbo: float | None
    status: CheckResult
    note: str = ""


def benjamini_hochberg(p_values: list[float]) -> list[float]:
    n = len(p_values)
    if n == 0:
        return []
    ranked = sorted(enumerate(p_values), key=lambda x: x[1])
    adj = [1.0] * n
    running = 1.0
    for k in range(n, 0, -1):
        idx, p = ranked[k - 1]
        running = min(running, p * n / k)
        adj[idx] = min(running, 1.0)
    return adj


def bonferroni(p_values: list[float]) -> list[float]:
    n = max(len(p_values), 1)
    return [min(p * n, 1.0) for p in p_values]


def holm(p_values: list[float]) -> list[float]:
    n = len(p_values)
    if n == 0:
        return []
    ranked = sorted(enumerate(p_values), key=lambda x: x[1])
    adj = [1.0] * n
    running = 0.0
    for rank, (idx, p) in enumerate(ranked):
        value = min(p * (n - rank), 1.0)
        running = max(running, value)
        adj[idx] = min(running, 1.0)
    return adj


def evaluate_family(
    p_values: list[float],
    *,
    method: CorrectionMethod = CorrectionMethod.BENJAMINI_HOCHBERG,
    alpha: float = 0.05,
) -> MultipleTestingReport:
    if not p_values:
        return MultipleTestingReport(
            n_hypotheses=0,
            method=method,
            alpha=alpha,
            status=CheckResult.NOT_TESTED,
            note="no p-values supplied",
        )
    if method is CorrectionMethod.BENJAMINI_HOCHBERG:
        adjusted = benjamini_hochberg(p_values)
    elif method is CorrectionMethod.BONFERRONI:
        adjusted = bonferroni(p_values)
    else:
        adjusted = holm(p_values)
    discoveries = sum(1 for a in adjusted if a <= alpha)
    return MultipleTestingReport(
        n_hypotheses=len(p_values),
        method=method,
        alpha=alpha,
        adjusted=adjusted,
        discoveries=discoveries,
        status=CheckResult.PASS,
        note="correction is diagnostic; it does not imply economic significance",
    )


def deflated_sharpe(
    sharpe: float,
    *,
    n_trials: int,
    n_periods: int,
    skew: float = 0.0,
    excess_kurtosis: float = 0.0,
) -> DeflatedSharpeReport:
    """Bailey / López de Prado deflated Sharpe. Returns NOT_TESTED if under-identified."""
    if n_trials < 2 or n_periods < 2:
        return DeflatedSharpeReport(
            naive_sharpe=sharpe,
            deflated_sharpe=None,
            n_trials=n_trials,
            n_periods=n_periods,
            status=CheckResult.NOT_TESTED,
            note="need n_trials>=2 and n_periods>=2",
        )
    sr = sharpe
    t = float(n_periods)
    inside = (1.0 - skew * sr + (excess_kurtosis / 4.0) * sr * sr) / (t - 1.0)
    if inside <= 0.0 or not math.isfinite(inside):
        return DeflatedSharpeReport(
            naive_sharpe=sharpe,
            deflated_sharpe=None,
            n_trials=n_trials,
            n_periods=n_periods,
            status=CheckResult.NOT_TESTED,
            note="standard error of Sharpe is undefined for this sample",
        )
    se = math.sqrt(inside)
    if se <= 0 or not math.isfinite(se):
        return DeflatedSharpeReport(
            naive_sharpe=sharpe,
            deflated_sharpe=None,
            n_trials=n_trials,
            n_periods=n_periods,
            status=CheckResult.NOT_TESTED,
            note="standard error of Sharpe is undefined",
        )
    euler = 0.5772156649015329
    expected_max = (1.0 - euler) * normal_ppf(1.0 - 1.0 / n_trials) + euler * normal_ppf(
        1.0 - 1.0 / (n_trials * math.e)
    )
    dsr = (sr - expected_max) / se
    return DeflatedSharpeReport(
        naive_sharpe=sharpe,
        deflated_sharpe=dsr,
        n_trials=n_trials,
        n_periods=n_periods,
        status=CheckResult.PASS,
        note="DSR is a multiple-testing-aware diagnostic, not a live-trading score",
    )


def probability_of_backtest_overfitting(
    trial_is: list[float],
    trial_oos: list[float],
) -> OverfittingReport:
    """Combinatorial PBO requires paired IS/OOS metrics across many trials."""
    n = min(len(trial_is), len(trial_oos))
    if n < 8:
        return OverfittingReport(
            n_trials=n,
            selection="max_is_sharpe",
            pbo=None,
            status=CheckResult.NOT_TESTED,
            note="PBO/CSCV needs at least 8 paired IS/OOS trials; not manufactured",
        )
    best = max(range(n), key=lambda i: trial_is[i])
    pbo = 1.0 if trial_oos[best] < 0 else 0.0
    return OverfittingReport(
        n_trials=n,
        selection="max_is_sharpe",
        pbo=pbo,
        status=CheckResult.WARN,
        note="simplified PBO proxy (best-IS negative OOS). Full CSCV is future work.",
    )
