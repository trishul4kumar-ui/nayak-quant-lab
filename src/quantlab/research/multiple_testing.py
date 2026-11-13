"""Multiple-testing corrections and deflated-Sharpe / PBO architecture.

A strategy found after many trials is not equivalent to a pre-registered test.
"""

from __future__ import annotations

import math
from enum import StrEnum
from itertools import combinations

from pydantic import BaseModel, Field

from quantlab.domain.research import CheckResult


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
    naive_sharpe: float | None
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
    n_blocks: int = 0
    n_observations: int = 0
    n_splits: int = 0
    logits: list[float] = Field(default_factory=list)


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
    """Do not calculate DSR without identified family and selection evidence.

    This legacy interface lacks the variance of trial Sharpe estimates, an
    independent/effective trial count and a verified selection record. The
    supplied moment parameters are retained for compatibility only: they do
    not identify a DSR by themselves. A former implementation emitted a
    standardized statistic as though it were the probabilistic DSR.
    """
    return DeflatedSharpeReport(
        naive_sharpe=sharpe if math.isfinite(sharpe) else None,
        deflated_sharpe=None,
        n_trials=n_trials,
        n_periods=n_periods,
        status=CheckResult.NOT_TESTED,
        note=(
            "DSR unavailable: trial Sharpe variance, independent/effective trial "
            "count, verified selection and identified return moments are required; "
            "the current interface does not establish them"
        ),
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
    return OverfittingReport(
        n_trials=n,
        selection="max_is_sharpe",
        pbo=None,
        status=CheckResult.NOT_TESTED,
        note="one pair of aggregate IS/OOS vectors cannot identify CSCV PBO",
    )


def cscv_overfitting(
    trial_returns: list[list[float]], *, n_blocks: int = 8
) -> OverfittingReport:
    """Estimate selection PBO from aligned periodic returns using mean return.

    Each row is a trial and each column the same ordered observation. Equal
    contiguous blocks are recombined into every half/half split. OOS ties use
    midranks; an IS winner tie is rejected rather than arbitrarily selected.
    This is descriptive research evidence, not independent OOS validation.
    """
    n_trials = len(trial_returns)
    n_observations = len(trial_returns[0]) if trial_returns else 0

    def unavailable(reason: str) -> OverfittingReport:
        return OverfittingReport(
            n_trials=n_trials,
            selection="cscv_max_mean_return",
            pbo=None,
            status=CheckResult.NOT_TESTED,
            note=reason,
            n_blocks=n_blocks,
            n_observations=n_observations,
        )

    if n_trials < 2:
        return unavailable("CSCV requires at least two complete trials")
    if n_blocks < 4 or n_blocks > 16 or n_blocks % 2:
        return unavailable("CSCV requires an even block count from 4 through 16")
    if n_observations < n_blocks * 2 or n_observations % n_blocks:
        return unavailable("CSCV requires equal blocks with at least two observations each")
    if any(len(trial) != n_observations for trial in trial_returns):
        return unavailable("CSCV requires the same observations for every trial")
    if any(not math.isfinite(value) for trial in trial_returns for value in trial):
        return unavailable("CSCV requires finite returns for every trial and observation")

    block_size = n_observations // n_blocks
    block_totals = [
        [sum(trial[i * block_size : (i + 1) * block_size]) for i in range(n_blocks)]
        for trial in trial_returns
    ]
    logits: list[float] = []
    all_blocks = set(range(n_blocks))
    for train_tuple in combinations(range(n_blocks), n_blocks // 2):
        train = set(train_tuple)
        test = all_blocks - train
        is_scores = [sum(totals[i] for i in train_tuple) for totals in block_totals]
        best = max(is_scores)
        winners = [index for index, score in enumerate(is_scores) if score == best]
        if len(winners) != 1:
            return unavailable("CSCV IS selection has tied winners; no arbitrary winner chosen")
        winner = winners[0]
        oos_scores = [sum(totals[i] for i in sorted(test)) for totals in block_totals]
        selected = oos_scores[winner]
        less = sum(score < selected for score in oos_scores)
        equal = sum(score == selected for score in oos_scores)
        rank = less + (equal + 1) / 2.0
        relative_rank = rank / (n_trials + 1)
        logits.append(math.log(relative_rank / (1.0 - relative_rank)))

    return OverfittingReport(
        n_trials=n_trials,
        selection="cscv_max_mean_return",
        pbo=sum(value <= 0 for value in logits) / len(logits),
        status=CheckResult.WARN,
        note=(
            "CSCV mean-return selection diagnostic only; it is not independent OOS "
            "validation or evidence of tradability. Results require aligned, complete "
            "trial histories, and incomplete trial families bias the estimate."
        ),
        n_blocks=n_blocks,
        n_observations=n_observations,
        n_splits=len(logits),
        logits=logits,
    )
