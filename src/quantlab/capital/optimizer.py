"""Capital optimizer wrapping existing mean-variance / ERC. Constraints stay explicit."""

from __future__ import annotations

import numpy as np

from quantlab.capital.errors import InfeasibleCapitalAllocation
from quantlab.core.errors import OptimizationError
from quantlab.portfolio.covariance import CovarianceReport, as_array
from quantlab.portfolio.optimize import (
    equal_risk_contribution,
    mean_variance_closed_form,
    min_variance_closed_form,
    min_variance_long_only,
)


def mean_variance_weights(
    names: list[str],
    mu: dict[str, float],
    cov: CovarianceReport,
    risk_aversion: float,
) -> dict[str, float]:
    vector = np.asarray([mu.get(name, 0.0) for name in names], dtype=np.float64)
    try:
        raw = mean_variance_closed_form(as_array(cov), vector, risk_aversion)
    except OptimizationError as exc:
        raise InfeasibleCapitalAllocation(
            str(exc),
            violated_constraints=["mean_variance"],
            required_adjustment="do not silently switch constructors",
            current_candidate={name: mu.get(name, 0.0) for name in names},
        ) from exc
    return {names[i]: float(raw[i]) for i in range(len(names))}


def min_variance_weights(
    names: list[str], cov: CovarianceReport, *, long_only: bool
) -> dict[str, float]:
    try:
        matrix = as_array(cov)
        raw = min_variance_long_only(matrix) if long_only else min_variance_closed_form(matrix)
    except OptimizationError as exc:
        raise InfeasibleCapitalAllocation(
            str(exc),
            violated_constraints=["min_variance"],
            required_adjustment="do not silently switch constructors",
        ) from exc
    return {names[i]: float(raw[i]) for i in range(len(names))}


def erc_weights(names: list[str], cov: CovarianceReport) -> dict[str, float]:
    try:
        raw = equal_risk_contribution(as_array(cov))
    except OptimizationError as exc:
        raise InfeasibleCapitalAllocation(
            str(exc),
            violated_constraints=["equal_risk_contribution"],
            required_adjustment="do not silently switch constructors",
        ) from exc
    return {names[i]: float(raw[i]) for i in range(len(names))}
