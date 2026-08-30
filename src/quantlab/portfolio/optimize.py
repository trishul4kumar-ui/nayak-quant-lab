from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

import numpy as np

from quantlab.core.errors import OptimizationError
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import ProposedPortfolio, Signal, TargetPosition


@runtime_checkable
class PortfolioOptimizer(Protocol):
    def weights(self, signals: list[Signal]) -> list[TargetPosition]: ...


class RankTopNLong:
    def __init__(self, top_n: int = 2, require_positive: bool = True) -> None:
        self.top_n = top_n
        self.require_positive = require_positive

    def weights(self, signals: list[Signal]) -> list[TargetPosition]:
        ranked = sorted(signals, key=lambda s: s.score, reverse=True)
        winners = ranked
        if self.require_positive:
            winners = [s for s in ranked if s.score > 0]
        winners = winners[: self.top_n]
        if not winners:
            return []
        weight = 1.0 / len(winners)
        return [TargetPosition(instrument=s.instrument, weight=weight) for s in winners]


class EqualWeight:
    def weights(self, signals: list[Signal]) -> list[TargetPosition]:
        if not signals:
            return []
        weight = 1.0 / len(signals)
        return [TargetPosition(instrument=s.instrument, weight=weight) for s in signals]


def construct_from_optimizer(
    optimizer: PortfolioOptimizer,
    signals: list[Signal],
    as_of: datetime,
    reason: str,
) -> ProposedPortfolio:
    return ProposedPortfolio(as_of=as_of, targets=optimizer.weights(signals), reason=reason)


def project_simplex(vector: np.ndarray) -> np.ndarray:
    """Euclidean projection onto {w ≥ 0, Σ w = 1}."""
    u = np.sort(vector)[::-1]
    cssv = np.cumsum(u) - 1.0
    rho = np.nonzero(u * np.arange(1, len(u) + 1) > cssv)[0]
    if len(rho) == 0:
        raise OptimizationError("simplex projection failed")
    theta = cssv[rho[-1]] / (rho[-1] + 1)
    projected = np.maximum(vector - theta, 0.0)
    total = float(projected.sum())
    if total <= 0:
        raise OptimizationError("simplex projection produced a zero vector")
    return np.asarray(projected / total, dtype=np.float64)


def min_variance_closed_form(cov: np.ndarray) -> np.ndarray:
    """Unconstrained Σ w = 1 min-var: w ∝ Σ⁻¹ 1. Uses inv, not pinv."""
    n = cov.shape[0]
    try:
        inv = np.linalg.inv(cov)
    except np.linalg.LinAlgError as exc:
        raise OptimizationError("covariance is singular") from exc
    raw = inv @ np.ones(n)
    total = float(raw.sum())
    if abs(total) < 1e-12:
        raise OptimizationError("min-var weights do not sum")
    if not np.isfinite(raw).all():
        raise OptimizationError("min-var produced non-finite weights")
    return np.asarray(raw / total, dtype=np.float64)


def min_variance_long_only(cov: np.ndarray, max_iter: int = 400) -> np.ndarray:
    """Projected gradient on the simplex. Not a commercial QP solver."""
    n = cov.shape[0]
    weights = np.full(n, 1.0 / n)
    scale = float(np.trace(cov)) + 1e-12
    step = 0.25 / scale
    for _ in range(max_iter):
        grad = 2.0 * (cov @ weights)
        nxt = project_simplex(weights - step * grad)
        if float(np.linalg.norm(nxt - weights)) < 1e-12:
            return nxt
        weights = nxt
    return weights


def mean_variance_closed_form(cov: np.ndarray, mu: np.ndarray, risk_aversion: float) -> np.ndarray:
    """Unconstrained: w ∝ Σ⁻¹ μ. μ is the documented alpha score, not future return."""
    if risk_aversion <= 0:
        raise OptimizationError("risk_aversion must be positive")
    try:
        inv = np.linalg.inv(cov)
    except np.linalg.LinAlgError as exc:
        raise OptimizationError("covariance is singular") from exc
    raw = inv @ mu
    if not np.isfinite(raw).all():
        raise OptimizationError("mean-variance produced non-finite weights")
    total = float(np.sum(np.abs(raw)))
    if total <= 0:
        raise OptimizationError("mean-variance weights are zero")
    summed = float(raw.sum())
    if abs(summed) > 1e-12:
        return np.asarray(raw / summed, dtype=np.float64)
    return np.asarray(raw / total, dtype=np.float64)


def equal_risk_contribution(cov: np.ndarray, max_iter: int = 400) -> np.ndarray:
    """Long-only ERC. RC_i = w_i (Σw)_i; target is equal share of w′Σw."""
    n = cov.shape[0]
    weights = np.full(n, 1.0 / n)
    for _ in range(max_iter):
        sigma2 = float(weights @ cov @ weights)
        if sigma2 <= 0:
            raise OptimizationError("ERC encountered non-positive variance")
        rc = weights * (cov @ weights)
        target = sigma2 / n
        nxt = weights * (target / (rc + 1e-18))
        nxt = project_simplex(nxt)
        if float(np.linalg.norm(nxt - weights)) < 1e-10:
            return nxt
        weights = nxt
    return weights


def array_to_targets(names: list[str], weights: np.ndarray) -> list[TargetPosition]:
    if not np.isfinite(weights).all():
        raise OptimizationError("optimizer produced non-finite weights")
    return [
        TargetPosition(instrument=InstrumentId.parse(names[i]), weight=float(weights[i]))
        for i in range(len(names))
        if abs(float(weights[i])) > 1e-12
    ]
