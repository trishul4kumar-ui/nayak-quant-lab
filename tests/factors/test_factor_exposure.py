"""Missing factor exposures are not zeros. Hard max_beta without a value is infeasible."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quantlab.core.errors import InfeasiblePortfolio
from quantlab.domain.research import CheckResult
from quantlab.factors.exposure import (
    ExposureMatrix,
    active_exposures,
    portfolio_exposures,
)
from quantlab.portfolio.constraints import (
    ConstraintHardness,
    ConstraintKind,
    ConstraintSpec,
    apply_constraints,
)


@pytest.mark.factor
def test_missing_exposure_is_none_not_zero() -> None:
    matrix = ExposureMatrix(
        as_of=datetime(2024, 1, 2, tzinfo=UTC),
        names=["NSE:AAA", "NSE:BBB"],
        factor_ids=["market_ew_beta"],
        matrix=[[1.0], [None]],
    )
    report = portfolio_exposures({"NSE:AAA": 0.5, "NSE:BBB": 0.5}, matrix)
    assert report.missing
    assert "NSE:BBB:market_ew_beta" in report.missing
    assert report.status is CheckResult.WARN


@pytest.mark.factor
def test_unknown_max_beta_is_infeasible() -> None:
    weights = {"NSE:AAA": 0.5, "NSE:BBB": 0.5}
    specs = [
        ConstraintSpec(
            constraint_id="beta",
            kind=ConstraintKind.MAX_BETA,
            hardness=ConstraintHardness.HARD,
            upper=0.5,
            tag="market_ew_beta",
        )
    ]
    with pytest.raises(InfeasiblePortfolio, match="unknown"):
        apply_constraints(weights, specs)
    with pytest.raises(InfeasiblePortfolio, match="unknown"):
        apply_constraints(weights, specs, portfolio_exposures={})


@pytest.mark.factor
def test_known_beta_constraint_enforced() -> None:
    weights = {"NSE:AAA": 1.0}
    specs = [
        ConstraintSpec(
            constraint_id="beta",
            kind=ConstraintKind.MAX_BETA,
            hardness=ConstraintHardness.HARD,
            upper=0.2,
            tag="market_ew_beta",
        )
    ]
    with pytest.raises(InfeasiblePortfolio, match="max_beta"):
        apply_constraints(weights, specs, portfolio_exposures={"market_ew_beta": 0.9})
    result = apply_constraints(weights, specs, portfolio_exposures={"market_ew_beta": 0.1})
    assert result.feasible


@pytest.mark.factor
def test_active_exposure_does_not_zero_missing() -> None:
    as_of = datetime(2024, 1, 2, tzinfo=UTC)
    from quantlab.factors.exposure import PortfolioFactorExposure

    port = PortfolioFactorExposure(as_of=as_of, exposures={"market_ew_beta": 0.4})
    bench = PortfolioFactorExposure(as_of=as_of, exposures={"style_momentum_20": 0.1})
    active = active_exposures(port, bench)
    assert "market_ew_beta" in active.missing
    assert "style_momentum_20" in active.missing
    assert active.exposures == {}
