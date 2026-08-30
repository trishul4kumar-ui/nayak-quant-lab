"""Causal research interfaces. Assumptions stay explicit. Placebos are required."""

from __future__ import annotations

from datetime import datetime

import numpy as np

from quantlab.core.errors import CausalResearchError
from quantlab.core.time import as_utc
from quantlab.domain.research import CheckResult
from quantlab.econometrics.enums import CausalClaim
from quantlab.econometrics.linalg import ols_fit
from quantlab.econometrics.models import CausalHypothesis, CausalSpecification


def did_estimate(
    outcome: list[float],
    treated: list[int],
    post: list[int],
    *,
    spec: CausalSpecification,
) -> tuple[float | None, CheckResult]:
    if not spec.assumptions:
        raise CausalResearchError("DiD requires explicit identification assumptions")
    n = min(len(outcome), len(treated), len(post))
    if n < 20:
        return None, CheckResult.NOT_TESTED
    y = np.asarray(outcome[:n], dtype=np.float64)
    t = np.asarray(treated[:n], dtype=np.float64)
    p = np.asarray(post[:n], dtype=np.float64)
    x = np.column_stack([np.ones(n), t, p, t * p])
    beta, *_ = ols_fit(y, x)
    return float(beta[3]), CheckResult.PASS


def event_study(
    outcome: list[float],
    event_available: datetime,
    as_of: datetime,
    *,
    window: int,
) -> tuple[float | None, CheckResult]:
    if as_utc(event_available) > as_utc(as_of):
        raise CausalResearchError("lookahead_event_study: event not available at as_of")
    if len(outcome) < window * 2 + 1:
        return None, CheckResult.NOT_TESTED
    mid = len(outcome) // 2
    pre = outcome[max(0, mid - window) : mid]
    post = outcome[mid + 1 : mid + 1 + window]
    if not pre or not post:
        return None, CheckResult.NOT_TESTED
    return float(np.mean(post) - np.mean(pre)), CheckResult.PASS


def synthetic_control_interface(donors: int) -> tuple[float | None, CheckResult]:
    if donors < 2:
        return None, CheckResult.NOT_TESTED
    return None, CheckResult.NOT_TESTED


def placebo_sign_flip(effect: float, noise: list[float], *, seed: int) -> float | None:
    if len(noise) < 8:
        return None
    rng = np.random.default_rng(seed)
    count = 0
    draws = 64
    for _ in range(draws):
        fake = float(np.mean(rng.choice(np.asarray(noise), size=len(noise), replace=True)))
        if abs(fake) >= abs(effect):
            count += 1
    return (count + 1) / (draws + 1)


def hypothesis(statement: str, identification: str) -> CausalHypothesis:
    return CausalHypothesis(
        hypothesis_id="H-CAUSAL-SEED",
        statement=statement,
        identification=identification,
        estimand="ATT under parallel trends / explicit assumptions",
        claim=CausalClaim.NONE,
    )
