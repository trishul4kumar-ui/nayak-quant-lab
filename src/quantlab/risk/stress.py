"""Explicit stress scenarios. Results are not forecasts."""

from __future__ import annotations

import numpy as np
from pydantic import BaseModel, Field

from quantlab.core.errors import CovarianceError
from quantlab.domain.research import CheckResult
from quantlab.portfolio.covariance import CovarianceReport, as_array
from quantlab.portfolio.risk_model import portfolio_variance


class StressScenario(BaseModel):
    scenario_id: str
    kind: str
    description: str
    vol_shock: float = 0.0
    corr_level: float | None = None
    returns: dict[str, float] = Field(default_factory=dict)


class StressResult(BaseModel):
    schema_version: str = "1"
    scenario_id: str
    kind: str
    pnl: float | None = None
    stressed_variance: float | None = None
    status: CheckResult = CheckResult.PASS
    note: str = "stress is a scenario, not a forecast"


def parametric_vol_shock(cov: CovarianceReport, shock: float) -> CovarianceReport:
    """Scale variances and covariances by (1+shock)^2. shock=-0.5 is a 50% vol cut."""
    scale = (1.0 + shock) ** 2
    if scale < 0:
        raise CovarianceError("vol shock produced a negative scale")
    matrix = as_array(cov) * scale
    return cov.model_copy(update={"matrix": matrix.tolist(), "note": f"vol_shock={shock}"})


def parametric_corr_shock(cov: CovarianceReport, corr: float) -> CovarianceReport:
    if not -1.0 <= corr <= 1.0:
        raise CovarianceError("correlation shock must be in [-1, 1]")
    sigma = as_array(cov)
    n = sigma.shape[0]
    vol = np.sqrt(np.clip(np.diag(sigma), 0.0, None))
    stressed = np.outer(vol, vol) * corr
    for i in range(n):
        stressed[i, i] = float(sigma[i, i])
    return cov.model_copy(update={"matrix": stressed.tolist(), "note": f"corr_shock={corr}"})


def apply_return_shock(weights: dict[str, float], returns: dict[str, float]) -> float:
    return sum(weights.get(k, 0.0) * returns.get(k, 0.0) for k in set(weights) | set(returns))


def run_stress(
    weights: dict[str, float],
    cov: CovarianceReport,
    scenario: StressScenario,
) -> StressResult:
    if scenario.kind == "vol_shock":
        stressed = parametric_vol_shock(cov, scenario.vol_shock)
        return StressResult(
            scenario_id=scenario.scenario_id,
            kind=scenario.kind,
            stressed_variance=portfolio_variance(weights, stressed),
            note=f"parametric vol shock {scenario.vol_shock}; not a forecast",
        )
    if scenario.kind == "corr_shock":
        if scenario.corr_level is None:
            raise CovarianceError("corr_shock requires corr_level")
        stressed = parametric_corr_shock(cov, scenario.corr_level)
        return StressResult(
            scenario_id=scenario.scenario_id,
            kind=scenario.kind,
            stressed_variance=portfolio_variance(weights, stressed),
            note=f"parametric corr={scenario.corr_level}; not a forecast",
        )
    if scenario.kind == "historical_returns":
        pnl = apply_return_shock(weights, scenario.returns)
        return StressResult(
            scenario_id=scenario.scenario_id,
            kind=scenario.kind,
            pnl=pnl,
            note="historical return vector applied to current weights; not a forecast",
        )
    return StressResult(
        scenario_id=scenario.scenario_id,
        kind=scenario.kind,
        status=CheckResult.NOT_TESTED,
        note=f"unknown scenario kind {scenario.kind}",
    )


def seed_scenarios() -> list[StressScenario]:
    return [
        StressScenario(
            scenario_id="vol_up_50",
            kind="vol_shock",
            description="Scale PIT covariance as if vol rose 50%",
            vol_shock=0.5,
        ),
        StressScenario(
            scenario_id="corr_one",
            kind="corr_shock",
            description="Force pairwise correlation to 1 keeping variances",
            corr_level=1.0,
        ),
    ]
