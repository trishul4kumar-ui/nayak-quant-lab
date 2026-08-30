"""Error-correction representation from Engle-Granger. Not a second Johansen engine."""

from __future__ import annotations

import numpy as np

from quantlab.domain.research import CheckResult
from quantlab.econometrics.linalg import ols_fit
from quantlab.econometrics.models import VECMSpecification
from quantlab.econometrics.stationarity import difference


def error_correction(
    y: list[float], x: list[float], beta: float
) -> tuple[VECMSpecification, float | None]:
    if min(len(y), len(x)) < 30:
        return (
            VECMSpecification(spec_id="vecm-eg", lags=1, status=CheckResult.NOT_TESTED),
            None,
        )
    n = min(len(y), len(x))
    left = np.asarray(y[-n:], dtype=np.float64)
    right = np.asarray(x[-n:], dtype=np.float64)
    ect = left[:-1] - beta * right[:-1]
    dy = np.asarray(difference(left.tolist()), dtype=np.float64)
    if len(dy) != len(ect):
        ect = ect[: len(dy)]
    design = np.column_stack([np.ones(len(dy)), ect])
    coef, *_ = ols_fit(dy, design)
    spec = VECMSpecification(
        spec_id="vecm-eg",
        lags=1,
        rank=1,
        status=CheckResult.PASS,
        note="ECM from Engle-Granger residual. Not Johansen rank.",
    )
    return spec, float(coef[1])
