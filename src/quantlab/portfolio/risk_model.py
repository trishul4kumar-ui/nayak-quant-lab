"""Risk diagnostics. The risk model must not secretly encode future returns."""

from __future__ import annotations

import math

import numpy as np
from pydantic import BaseModel, Field

from quantlab.core.errors import OptimizationError
from quantlab.domain.research import CheckResult
from quantlab.portfolio.covariance import CovarianceReport, as_array


class RiskContribution(BaseModel):
    security_id: str
    weight: float
    marginal: float | None = None
    component: float | None = None


class RiskDiagnostics(BaseModel):
    schema_version: str = "1"
    volatility: float | None = None
    contributions: list[RiskContribution] = Field(default_factory=list)
    vol_scale: float = 1.0
    status: CheckResult = CheckResult.PASS
    note: str = "σ = sqrt(w′Σw) from PIT covariance; not future realized vol"


def portfolio_variance(weights: dict[str, float], cov: CovarianceReport) -> float:
    w = _align(weights, cov.names)
    sigma2 = float(w.T @ as_array(cov) @ w)
    if sigma2 < -1e-12:
        raise OptimizationError("negative portfolio variance")
    return max(sigma2, 0.0)


def portfolio_volatility(weights: dict[str, float], cov: CovarianceReport) -> float:
    return math.sqrt(portfolio_variance(weights, cov))


def risk_contributions(weights: dict[str, float], cov: CovarianceReport) -> RiskDiagnostics:
    names = cov.names
    w = _align(weights, names)
    sigma = math.sqrt(max(float(w.T @ as_array(cov) @ w), 0.0))
    if sigma <= 0:
        return RiskDiagnostics(
            volatility=0.0,
            contributions=[
                RiskContribution(security_id=n, weight=float(w[i])) for i, n in enumerate(names)
            ],
            status=CheckResult.NOT_TESTED,
            note="zero portfolio volatility",
        )
    mcr = as_array(cov) @ w / sigma
    crc = w * mcr
    contribs = [
        RiskContribution(
            security_id=names[i],
            weight=float(w[i]),
            marginal=float(mcr[i]),
            component=float(crc[i]),
        )
        for i in range(len(names))
    ]
    return RiskDiagnostics(volatility=sigma, contributions=contribs)


def apply_vol_target(
    weights: dict[str, float],
    cov: CovarianceReport,
    target: float,
    max_leverage: float,
) -> tuple[dict[str, float], float]:
    if target <= 0:
        raise OptimizationError("vol_target must be positive")
    sigma = portfolio_volatility(weights, cov)
    if sigma <= 0:
        raise OptimizationError("cannot vol-target a zero-volatility portfolio")
    scale = min(target / sigma, max_leverage)
    scaled = {k: v * scale for k, v in weights.items()}
    return scaled, scale


def _align(weights: dict[str, float], names: list[str]) -> np.ndarray:
    return np.asarray([weights.get(name, 0.0) for name in names], dtype=np.float64)
