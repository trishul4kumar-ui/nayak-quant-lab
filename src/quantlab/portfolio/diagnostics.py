"""Portfolio sanity diagnostics. A successful solve is not a research result."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.core.errors import CovarianceError, OptimizationError
from quantlab.domain.research import CheckResult
from quantlab.portfolio.covariance import CovarianceReport
from quantlab.portfolio.exposures import ExposureReport, exposure_report
from quantlab.portfolio.risk_model import RiskDiagnostics, risk_contributions
from quantlab.portfolio.turnover import two_sided_turnover


class PortfolioDiagnostics(BaseModel):
    schema_version: str = "1"
    n_positions: int = 0
    gross: float = 0.0
    net: float = 0.0
    cash: float = 0.0
    max_weight: float = 0.0
    turnover: float = 0.0
    concentration_hhi: float | None = None
    effective_n: float | None = None
    estimated_volatility: float | None = None
    vol_scale: float = 1.0
    exposures: ExposureReport = Field(default_factory=ExposureReport)
    risk: RiskDiagnostics | None = None
    constructor: str = ""
    optimizer_status: str = "baseline"
    note: str = "target weights are not orders"


def diagnose(
    weights: dict[str, float],
    *,
    prev: dict[str, float] | None = None,
    cov: CovarianceReport | None = None,
    constructor: str = "",
    optimizer_status: str = "baseline",
    vol_scale: float = 1.0,
) -> PortfolioDiagnostics:
    exp = exposure_report(weights)
    risk = None
    vol = None
    if cov is not None and cov.names:
        try:
            risk = risk_contributions(weights, cov)
            vol = risk.volatility
        except (OptimizationError, CovarianceError):
            risk = RiskDiagnostics(status=CheckResult.NOT_TESTED, note="risk diagnostics failed")
    return PortfolioDiagnostics(
        n_positions=exp.n_positions,
        gross=exp.gross,
        net=exp.net,
        cash=exp.cash,
        max_weight=exp.max_weight,
        turnover=two_sided_turnover(prev or {}, weights),
        concentration_hhi=exp.hhi,
        effective_n=exp.effective_n,
        estimated_volatility=vol,
        vol_scale=vol_scale,
        exposures=exp,
        risk=risk,
        constructor=constructor,
        optimizer_status=optimizer_status,
    )
