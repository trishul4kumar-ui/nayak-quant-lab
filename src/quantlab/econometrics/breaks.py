"""CUSUM and rolling-coefficient stability. Known-break tests stay explicit."""

from __future__ import annotations

import numpy as np

from quantlab.domain.research import CheckResult
from quantlab.econometrics.enums import BreakKind
from quantlab.econometrics.linalg import ols_fit
from quantlab.econometrics.models import StructuralBreakTest


def cusum(values: list[float]) -> StructuralBreakTest:
    series = np.asarray(values, dtype=np.float64)
    n = len(series)
    if n < 30:
        return StructuralBreakTest(
            kind=BreakKind.CUSUM,
            statistic=None,
            break_index=None,
            status=CheckResult.NOT_TESTED,
            note="CUSUM needs a longer window.",
        )
    x = np.column_stack([np.ones(n), np.arange(n, dtype=np.float64)])
    _, resid, _ = ols_fit(series, x)
    sigma = float(np.std(resid))
    if sigma <= 0:
        return StructuralBreakTest(
            kind=BreakKind.CUSUM,
            statistic=None,
            break_index=None,
            status=CheckResult.NOT_TESTED,
            note="CUSUM residual variance is zero.",
        )
    walk = np.cumsum(resid) / (sigma * np.sqrt(n))
    idx = int(np.argmax(np.abs(walk)))
    return StructuralBreakTest(
        kind=BreakKind.CUSUM,
        statistic=float(np.max(np.abs(walk))),
        break_index=idx,
        status=CheckResult.PASS,
        note="CUSUM of OLS residuals. A peak is a research flag, not an automatic regime model.",
    )


def rolling_stability(values: list[float], *, window: int = 24) -> StructuralBreakTest:
    series = np.asarray(values, dtype=np.float64)
    if len(series) < window + 5:
        return StructuralBreakTest(
            kind=BreakKind.ROLLING,
            statistic=None,
            break_index=None,
            status=CheckResult.NOT_TESTED,
            note="Rolling coefficient stability needs a longer window.",
        )
    coefs = []
    for start in range(0, len(series) - window + 1):
        chunk = series[start : start + window]
        x = np.column_stack([np.ones(window), np.arange(window, dtype=np.float64)])
        beta, *_ = ols_fit(chunk, x)
        coefs.append(float(beta[1]))
    spread = float(np.std(np.asarray(coefs)))
    return StructuralBreakTest(
        kind=BreakKind.ROLLING,
        statistic=spread,
        break_index=int(np.argmax(np.abs(np.diff(coefs)))) if len(coefs) > 1 else 0,
        status=CheckResult.PASS,
        note="Rolling slope dispersion. Not a Chow test and not a live halt.",
    )
