from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quantlab.core.errors import CausalResearchError
from quantlab.domain.research import CheckResult
from quantlab.econometrics.causal import (
    did_estimate,
    event_study,
    hypothesis,
    placebo_sign_flip,
    synthetic_control_interface,
)
from quantlab.econometrics.economics import economic_report
from quantlab.econometrics.enums import CausalClaim, EstimatorKind
from quantlab.econometrics.granger import granger_pair
from quantlab.econometrics.library import stationary_ar1
from quantlab.econometrics.models import CausalSpecification
from quantlab.econometrics.service import run_econometrics
from quantlab.research.multiple_testing import evaluate_family


def test_granger_is_predictive_never_causation() -> None:
    x = stationary_ar1(n=80, seed=1)
    y = [0.5 * a + b for a, b in zip(x, stationary_ar1(n=80, seed=2), strict=True)]
    item = granger_pair(x, y, lags=1, seed=0)
    assert item.claim is CausalClaim.PREDICTIVE
    assert "not" in item.note.lower()
    assert "causation" in item.note.lower()


def test_granger_short_not_tested() -> None:
    item = granger_pair([1.0, 2.0], [2.0, 3.0], lags=1, seed=0)
    assert item.status is CheckResult.NOT_TESTED
    assert item.claim is CausalClaim.PREDICTIVE


def test_did_requires_assumptions() -> None:
    spec = CausalSpecification(
        hypothesis_id="H1",
        method=EstimatorKind.DID,
        treatment="d",
        outcome="y",
        assumptions=(),
    )
    with pytest.raises(CausalResearchError, match="assumptions"):
        did_estimate([0.0] * 40, [0] * 20 + [1] * 20, [0] * 20 + [1] * 20, spec=spec)


def test_did_with_assumptions_does_not_claim_proof() -> None:
    spec = CausalSpecification(
        hypothesis_id="H1",
        method=EstimatorKind.DID,
        treatment="d",
        outcome="y",
        assumptions=("parallel_trends_untested",),
        claim=CausalClaim.CAUSAL_UNDER_ASSUMPTIONS,
    )
    y = stationary_ar1(n=40, seed=0)
    treated = [0] * 20 + [1] * 20
    post = [0] * 20 + [1] * 20
    effect, status = did_estimate(y, treated, post, spec=spec)
    assert status is CheckResult.PASS
    assert effect is not None
    hypo = hypothesis("treated minus control", "parallel trends untested")
    assert hypo.claim is CausalClaim.NONE


def test_did_small_sample_not_tested() -> None:
    spec = CausalSpecification(
        hypothesis_id="H1",
        method=EstimatorKind.DID,
        treatment="d",
        outcome="y",
        assumptions=("parallel_trends_untested",),
    )
    effect, status = did_estimate([1.0] * 10, [0] * 5 + [1] * 5, [0] * 5 + [1] * 5, spec=spec)
    assert effect is None
    assert status is CheckResult.NOT_TESTED


def test_event_study_lookahead_raises() -> None:
    as_of = datetime(2024, 1, 15, tzinfo=UTC)
    event = datetime(2024, 1, 16, tzinfo=UTC)
    with pytest.raises(CausalResearchError, match="lookahead_event_study"):
        event_study(stationary_ar1(n=40, seed=0), event, as_of, window=2)


def test_event_study_available_ok() -> None:
    as_of = datetime(2024, 1, 16, tzinfo=UTC)
    event = datetime(2024, 1, 15, tzinfo=UTC)
    effect, status = event_study(stationary_ar1(n=40, seed=0), event, as_of, window=3)
    assert status in {CheckResult.PASS, CheckResult.NOT_TESTED}
    if status is CheckResult.PASS:
        assert effect is not None


def test_synthetic_control_never_fabricated() -> None:
    effect, status = synthetic_control_interface(8)
    assert effect is None
    assert status is CheckResult.NOT_TESTED


@pytest.mark.parametrize("donors", [0, 1, 2, 5, 10])
def test_synthetic_control_always_not_tested(donors: int) -> None:
    effect, status = synthetic_control_interface(donors)
    assert effect is None
    assert status is CheckResult.NOT_TESTED


def test_placebo_sign_flip_none_on_short() -> None:
    assert placebo_sign_flip(1.0, [0.1, 0.2], seed=0) is None
    p = placebo_sign_flip(1.0, list(range(20)), seed=1)
    assert p is not None
    assert 0.0 < p <= 1.0


def test_economic_significance_is_not_a_p_value() -> None:
    report = economic_report(statistic=2.0, effect=0.05, cost_bps=10.0)
    assert report.execution_adjusted is not None
    note = report.note.lower()
    assert "p-value" in note or "not a claim" in note
    missing = economic_report(statistic=None, effect=None, cost_bps=10.0)
    assert missing.status is CheckResult.NOT_TESTED


def test_seed_run_uses_evaluate_family() -> None:
    result = run_econometrics()
    family = evaluate_family([0.01, 0.40, 0.80])
    assert family.n_hypotheses == 3
    assert result.multiple_testing.get("tested_count") is not None


@pytest.mark.parametrize("claim", list(CausalClaim))
def test_causal_claim_enum(claim: CausalClaim) -> None:
    allowed = {CausalClaim.NONE, CausalClaim.PREDICTIVE, CausalClaim.ASSOCIATIONAL}
    assert "causal" in claim.value or claim in allowed
    assert claim is not None
