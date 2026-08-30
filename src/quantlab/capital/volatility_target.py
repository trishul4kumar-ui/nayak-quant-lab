"""Volatility targeting bounded by leverage. Does not silently lever up."""

from __future__ import annotations

from pydantic import BaseModel

from quantlab.capital.definitions import VolTargetStatus
from quantlab.portfolio.covariance import CovarianceReport
from quantlab.portfolio.risk_model import apply_vol_target, portfolio_volatility


class VolTargetResult(BaseModel):
    weights: dict[str, float]
    scale: float
    estimated_vol: float | None
    target_vol: float
    status: VolTargetStatus
    note: str = ""


def target_volatility(
    weights: dict[str, float],
    cov: CovarianceReport | None,
    target: float,
    max_leverage: float,
) -> VolTargetResult:
    if cov is None:
        return VolTargetResult(
            weights=dict(weights),
            scale=1.0,
            estimated_vol=None,
            target_vol=target,
            status=VolTargetStatus.NOT_TESTED,
            note="covariance missing; vol target NOT_TESTED not zero",
        )
    sigma = portfolio_volatility(weights, cov)
    if sigma <= 0:
        return VolTargetResult(
            weights=dict(weights),
            scale=1.0,
            estimated_vol=sigma,
            target_vol=target,
            status=VolTargetStatus.NOT_TESTED,
            note="zero estimated vol; cannot target",
        )
    required = target / sigma
    scaled, scale = apply_vol_target(weights, cov, target, max_leverage)
    if required > max_leverage + 1e-12:
        return VolTargetResult(
            weights=scaled,
            scale=scale,
            estimated_vol=sigma,
            target_vol=target,
            status=VolTargetStatus.TARGET_UNACHIEVABLE,
            note="TARGET_UNACHIEVABLE: required scale exceeds leverage; not increased",
        )
    return VolTargetResult(
        weights=scaled,
        scale=scale,
        estimated_vol=sigma,
        target_vol=target,
        status=VolTargetStatus.ACHIEVED,
        note=f"gross_scaler={scale:.6f}",
    )
