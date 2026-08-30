"""Ensemble combination, sign convention, and missing-alpha policy."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quantlab.alpha.ensemble import (
    AlphaEnsemble,
    EnsembleComponent,
    EnsembleMethod,
    apply_sign,
    combine_alpha_panels,
    get_ensemble,
    score_sign,
)
from quantlab.core.errors import AlignmentError
from quantlab.portfolio.baselines import top_n_equal
from quantlab.portfolio.experiment import apply_missing_policy
from quantlab.portfolio.spec import MissingAlphaPolicy


@pytest.mark.portfolio
def test_seed_ensembles_are_versioned() -> None:
    mom = get_ensemble("mom20")
    combo = get_ensemble("mom_5_20")
    assert mom.identity_hash() != combo.identity_hash()
    assert [c.weight for c in combo.components] == [0.5, 0.5]


@pytest.mark.portfolio
def test_sign_is_not_flipped_for_sharpe() -> None:
    scores = {"NSE:A": 1.0, "NSE:B": -0.5}
    assert score_sign("long_high") == 1
    assert apply_sign(scores, "long_high") == scores
    inverted = apply_sign(scores, "long_low")
    assert inverted["NSE:A"] == -1.0
    assert inverted["NSE:B"] == 0.5


@pytest.mark.portfolio
def test_equal_weight_ensemble_averages_zscores() -> None:
    as_of = datetime(2024, 2, 1, tzinfo=UTC)
    ensemble = AlphaEnsemble(
        ensemble_id="toy",
        version="1",
        name="toy",
        components=[
            EnsembleComponent(alpha_id="rank_momentum_20", weight=1.0),
            EnsembleComponent(alpha_id="rank_momentum_5", weight=1.0),
        ],
        method=EnsembleMethod.EQUAL_WEIGHT,
    )
    left = {as_of: {"NSE:A": 1.0, "NSE:B": 2.0, "NSE:C": 3.0}}
    right = {as_of: {"NSE:A": 3.0, "NSE:B": 2.0, "NSE:C": 1.0}}
    combined = combine_alpha_panels(ensemble, [left, right])
    row = combined[as_of]
    assert set(row) == {"NSE:A", "NSE:B", "NSE:C"}
    assert abs(row["NSE:B"]) < abs(row["NSE:A"]) + 1.0


@pytest.mark.portfolio
def test_missing_alpha_exclude_does_not_fill_zero() -> None:
    row = {"NSE:A": 1.0, "NSE:B": 2.0}
    universe = ["NSE:A", "NSE:B", "NSE:C"]
    out = apply_missing_policy(row, universe, MissingAlphaPolicy.EXCLUDE)
    assert "NSE:C" not in out
    neutralized = apply_missing_policy(row, universe, MissingAlphaPolicy.NEUTRALIZE)
    assert neutralized.get("NSE:C") == 0.0


@pytest.mark.portfolio
def test_nan_scores_fail() -> None:
    with pytest.raises(AlignmentError, match="non-finite"):
        top_n_equal({"NSE:A": float("nan"), "NSE:B": 1.0, "NSE:C": 2.0}, 2)
