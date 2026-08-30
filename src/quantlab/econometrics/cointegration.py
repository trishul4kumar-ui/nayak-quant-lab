"""Engle-Granger cointegration. Johansen is an explicit NOT_TESTED interface."""

from __future__ import annotations

import numpy as np

from quantlab.domain.research import CheckResult
from quantlab.econometrics.enums import EstimatorKind
from quantlab.econometrics.linalg import as_vector, ols_fit
from quantlab.econometrics.models import CointegrationTest
from quantlab.econometrics.stationarity import adf_test


def engle_granger(y: list[float], x: list[float]) -> CointegrationTest:
    left = as_vector(y)
    right = as_vector(x)
    n = min(len(left), len(right))
    if n < 30:
        return CointegrationTest(
            method=EstimatorKind.ENGLE_GRANGER,
            statistic=None,
            beta=None,
            status=CheckResult.NOT_TESTED,
            note="Engle-Granger needs a longer overlap. Not a cointegration claim.",
        )
    left = left[-n:]
    right = right[-n:]
    design = np.column_stack([np.ones(n), right])
    beta, resid, _ = ols_fit(left, design)
    residual_adf = adf_test(resid.tolist())
    return CointegrationTest(
        method=EstimatorKind.ENGLE_GRANGER,
        statistic=residual_adf.statistic,
        beta=float(beta[1]),
        residual_adf=residual_adf,
        status=residual_adf.status,
        note=(
            "Engle-Granger residual ADF. A stationary residual is not a trading signal "
            "and is not Johansen rank."
        ),
    )


def johansen_interface(series: list[list[float]]) -> CointegrationTest:
    n = min((len(row) for row in series), default=0)
    return CointegrationTest(
        method=EstimatorKind.JOHANSEN,
        statistic=None,
        beta=None,
        status=CheckResult.NOT_TESTED,
        note=(
            f"{len(series)} series, n={n}. Johansen is not fabricated. "
            "Use Engle-Granger until a certified multivariate library is sourced."
        ),
    )
