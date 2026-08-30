"""Factor-model covariance Σ = B Ω Bᵀ + D when the inputs exist."""

from __future__ import annotations

import numpy as np
from pydantic import BaseModel

from quantlab.core.errors import CovarianceError
from quantlab.domain.research import CheckResult
from quantlab.factors.exposure import ExposureMatrix
from quantlab.portfolio.covariance import CovarianceReport, as_array
from quantlab.portfolio.risk_model import portfolio_variance


class FactorRiskReport(BaseModel):
    schema_version: str = "1"
    total_variance: float | None = None
    factor_variance: float | None = None
    idiosyncratic_variance: float | None = None
    factor_share: float | None = None
    status: CheckResult = CheckResult.NOT_TESTED
    note: str = "requires B and factor covariance; otherwise NOT_TESTED"


def idiosyncratic_diagonal(
    asset_cov: CovarianceReport,
    exposures: ExposureMatrix,
    factor_cov: np.ndarray,
) -> np.ndarray:
    """D = diag(Σ - B Ω Bᵀ) clipped at 0. Negative leftovers fail rather than hide."""
    if exposures.names != asset_cov.names:
        raise CovarianceError("exposure names must match asset covariance names")
    b = _b_array(exposures)
    systematic = b @ factor_cov @ b.T
    leftover = as_array(asset_cov) - systematic
    diag = np.diag(leftover)
    if np.any(diag < -1e-8):
        raise CovarianceError("idiosyncratic variance would be negative")
    return np.diag(np.clip(diag, 0.0, None))


def tracking_variance(
    active_weights: dict[str, float],
    asset_cov: CovarianceReport,
) -> float:
    """w_active′ Σ w_active. Not a forecast of tracking error."""
    return portfolio_variance(active_weights, asset_cov)


def decompose_portfolio_variance(
    weights: dict[str, float],
    asset_cov: CovarianceReport,
    exposures: ExposureMatrix | None = None,
    factor_cov: np.ndarray | None = None,
) -> FactorRiskReport:
    total = portfolio_variance(weights, asset_cov)
    if exposures is None or factor_cov is None or not exposures.names:
        return FactorRiskReport(
            total_variance=total,
            status=CheckResult.NOT_TESTED,
            note="factor decomposition requires B and Ω; reporting asset-level variance only",
        )
    b = _b_array(exposures)
    w = np.asarray([weights.get(n, 0.0) for n in exposures.names], dtype=np.float64)
    factor_var = float(w.T @ b @ factor_cov @ b.T @ w)
    d = idiosyncratic_diagonal(asset_cov, exposures, factor_cov)
    idio = float(w.T @ d @ w)
    share = None if total <= 0 else factor_var / total
    return FactorRiskReport(
        total_variance=total,
        factor_variance=factor_var,
        idiosyncratic_variance=idio,
        factor_share=share,
        status=CheckResult.PASS,
        note="Σ = BΩBᵀ + D; residual variance is not automatic alpha",
    )


def _b_array(exposures: ExposureMatrix) -> np.ndarray:
    rows: list[list[float]] = []
    for row in exposures.matrix:
        filled: list[float] = []
        for value in row:
            if value is None:
                raise CovarianceError("missing factor exposure is not filled with zero")
            filled.append(float(value))
        rows.append(filled)
    return np.asarray(rows, dtype=np.float64)
