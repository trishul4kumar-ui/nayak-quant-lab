"""ACF/PACF, Ljung-Box, and HAC lag choice. Residuals are never silently whitened."""

from __future__ import annotations

from quantlab.domain.research import CheckResult
from quantlab.econometrics.linalg import acf_values, as_vector, ljung_box, pacf_values
from quantlab.econometrics.models import DependenceDiagnostic


def dependence_report(values: list[float], *, nlags: int = 8) -> DependenceDiagnostic:
    series = as_vector(values)
    if len(series) < 8:
        return DependenceDiagnostic(
            status=CheckResult.NOT_TESTED,
            note="Dependence diagnostics need a longer residual window.",
        )
    used = min(nlags, max(len(series) // 8, 1))
    acf = acf_values(series, used)
    pacf = pacf_values(series, used)
    lb = ljung_box(series, used)
    return DependenceDiagnostic(
        acf=acf,
        pacf=pacf,
        ljung_box=lb,
        hac_lags=used,
        status=CheckResult.PASS if acf else CheckResult.NOT_TESTED,
        note="HAC/Newey-West lags equal the diagnostic window. Residuals are not 'fixed'.",
    )
