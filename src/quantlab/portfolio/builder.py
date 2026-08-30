"""Dispatch a PortfolioModel to a constructor. Optimization is optional."""

from __future__ import annotations

from datetime import datetime

import numpy as np

from quantlab.core.errors import OptimizationError
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import OHLCVBar, ProposedPortfolio
from quantlab.portfolio.baselines import (
    bottom_n_equal,
    equal_weight_names,
    long_short_top_bottom,
    rank_weight,
    score_weight,
    targets_to_map,
    top_n_equal,
)
from quantlab.portfolio.constraints import apply_constraints, to_targets
from quantlab.portfolio.covariance import CovarianceReport, as_array, sample_covariance
from quantlab.portfolio.optimize import (
    array_to_targets,
    equal_risk_contribution,
    mean_variance_closed_form,
    min_variance_closed_form,
    min_variance_long_only,
    project_simplex,
)
from quantlab.portfolio.risk_model import apply_vol_target
from quantlab.portfolio.spec import ConstructorKind, PortfolioModel


def is_rebalance(
    policy: str,
    as_of: datetime,
    prev_as_of: datetime | None,
    session_index: int,
) -> bool:
    if policy == "daily":
        return True
    if policy == "weekly":
        return session_index % 5 == 0
    if policy == "monthly":
        if prev_as_of is None:
            return True
        return as_of.month != prev_as_of.month or as_of.year != prev_as_of.year
    return True


def construct_targets(
    model: PortfolioModel,
    scores: dict[str, float],
    as_of: datetime,
    *,
    bars: dict[InstrumentId, list[OHLCVBar]] | None = None,
    prev_weights: dict[str, float] | None = None,
) -> tuple[ProposedPortfolio, CovarianceReport | None, str]:
    kind = model.constructor
    cov: CovarianceReport | None = None
    status = "baseline"
    if kind is ConstructorKind.TOP_N:
        targets = top_n_equal(scores, model.top_n)
    elif kind is ConstructorKind.BOTTOM_N:
        targets = bottom_n_equal(scores, model.bottom_n or model.top_n)
    elif kind is ConstructorKind.EQUAL_WEIGHT:
        targets = equal_weight_names(scores)
    elif kind is ConstructorKind.RANK_WEIGHT:
        targets = rank_weight(scores)
    elif kind is ConstructorKind.SCORE_WEIGHT:
        targets = score_weight(scores)
    elif kind is ConstructorKind.LONG_SHORT_TOP_BOTTOM:
        targets = long_short_top_bottom(scores, model.top_n, model.bottom_n or model.top_n)
    elif kind in {
        ConstructorKind.MIN_VARIANCE,
        ConstructorKind.MEAN_VARIANCE,
        ConstructorKind.RISK_PARITY,
    }:
        if bars is None:
            raise OptimizationError("optimizer constructors require PIT bars and as_of")
        names = sorted(scores)
        cov = sample_covariance(
            bars,
            as_of,
            names,
            model.covariance_lookback,
            repair=model.covariance_repair,
        )
        matrix = as_array(cov)
        aligned = cov.names
        if kind is ConstructorKind.MIN_VARIANCE:
            raw = (
                min_variance_long_only(matrix)
                if model.long_only
                else min_variance_closed_form(matrix)
            )
            status = "min_variance"
        elif kind is ConstructorKind.MEAN_VARIANCE:
            mu = np.asarray([scores.get(n, 0.0) for n in aligned], dtype=np.float64)
            raw = mean_variance_closed_form(matrix, mu, model.risk_aversion)
            if model.long_only:
                raw = project_simplex(raw)
            status = "mean_variance"
        else:
            if not model.long_only:
                raise OptimizationError("risk parity is implemented long-only only")
            raw = equal_risk_contribution(matrix)
            status = "risk_parity"
        targets = array_to_targets(aligned, raw)
    else:
        raise OptimizationError(f"unsupported constructor {kind}")

    weights = targets_to_map(targets)
    if model.vol_target is not None:
        if cov is None:
            if bars is None:
                raise OptimizationError("vol targeting requires PIT covariance")
            cov = sample_covariance(
                bars,
                as_of,
                sorted(weights),
                model.covariance_lookback,
                repair=model.covariance_repair,
            )
        weights, _scale = apply_vol_target(weights, cov, model.vol_target, model.max_leverage)
    checked = apply_constraints(weights, model.constraints, prev_weights=prev_weights)
    proposal = ProposedPortfolio(
        as_of=as_of,
        targets=to_targets(checked.weights),
        reason=f"{model.portfolio_id}:{kind.value}",
    )
    return proposal, cov, status
