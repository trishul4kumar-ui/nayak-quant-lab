"""Transparent constructors, constraints, turnover, and concentration."""

from __future__ import annotations

import math

import pytest

from quantlab.core.errors import InfeasiblePortfolio
from quantlab.portfolio.baselines import (
    equal_weight_names,
    long_short_top_bottom,
    rank_weight,
    targets_to_map,
    top_n_equal,
)
from quantlab.portfolio.constraints import (
    ConstraintHardness,
    ConstraintKind,
    ConstraintSpec,
    apply_constraints,
    long_only_set,
)
from quantlab.portfolio.exposures import exposure_report
from quantlab.portfolio.turnover import two_sided_turnover

SCORES = {"NSE:AAA": 0.4, "NSE:BBB": 0.2, "NSE:CCC": 0.1, "NSE:DDD": -0.1, "NSE:EEE": -0.3}


@pytest.mark.portfolio
def test_top_n_long_only_sums_to_one() -> None:
    weights = targets_to_map(top_n_equal(SCORES, 2))
    assert math.isclose(sum(weights.values()), 1.0, abs_tol=1e-9)
    assert all(v > 0 for v in weights.values())
    assert len(weights) == 2


@pytest.mark.portfolio
def test_long_short_gross_and_net() -> None:
    weights = targets_to_map(long_short_top_bottom(SCORES, 2, 2))
    gross = sum(abs(v) for v in weights.values())
    net = sum(weights.values())
    assert math.isclose(gross, 1.0, abs_tol=1e-9)
    assert abs(net) < 1e-9
    assert any(v < 0 for v in weights.values())


@pytest.mark.portfolio
def test_rank_weight_is_long_only_and_sums() -> None:
    weights = targets_to_map(rank_weight(SCORES))
    assert math.isclose(sum(weights.values()), 1.0, abs_tol=1e-9)
    assert all(v >= 0 for v in weights.values())


@pytest.mark.portfolio
def test_equal_weight_and_hhi() -> None:
    weights = targets_to_map(equal_weight_names(SCORES))
    exp = exposure_report(weights)
    assert math.isclose(exp.gross, 1.0, abs_tol=1e-9)
    assert exp.hhi == pytest.approx(0.2)
    assert exp.effective_n == pytest.approx(5.0)
    assert exp.beta.value == "not_tested"


@pytest.mark.portfolio
def test_turnover_is_half_l1() -> None:
    prev = {"NSE:A": 0.5, "NSE:B": 0.5}
    new = {"NSE:A": 1.0}
    assert two_sided_turnover(prev, new) == pytest.approx(0.5)
    assert two_sided_turnover({}, {"NSE:A": 1.0}) == pytest.approx(0.5)


@pytest.mark.portfolio
def test_hard_max_weight_is_infeasible_not_relaxed() -> None:
    weights = {"NSE:A": 0.6, "NSE:B": 0.4}
    specs = [
        ConstraintSpec(
            constraint_id="cap",
            kind=ConstraintKind.MAX_WEIGHT,
            hardness=ConstraintHardness.HARD,
            upper=0.5,
        )
    ]
    with pytest.raises(InfeasiblePortfolio, match="max_weight"):
        apply_constraints(weights, specs)


@pytest.mark.portfolio
def test_soft_constraint_warns_only() -> None:
    weights = {"NSE:A": 0.6, "NSE:B": 0.4}
    specs = [
        ConstraintSpec(
            constraint_id="cap",
            kind=ConstraintKind.MAX_WEIGHT,
            hardness=ConstraintHardness.SOFT,
            upper=0.5,
        )
    ]
    result = apply_constraints(weights, specs)
    assert result.feasible
    assert result.warnings
    assert result.weights["NSE:A"] == 0.6


@pytest.mark.portfolio
def test_default_long_only_set_caps_name_weight() -> None:
    with pytest.raises(InfeasiblePortfolio):
        apply_constraints({"NSE:A": 0.7, "NSE:B": 0.3}, long_only_set())
