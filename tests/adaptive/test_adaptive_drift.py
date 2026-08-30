"""Drift, decay, and ensemble constraints."""

from __future__ import annotations

import pytest

from quantlab.adaptive.decay import estimate_half_life
from quantlab.adaptive.definition import AdaptationPolicy, AdaptiveModelDefinition, LearnerKind
from quantlab.adaptive.drift import classify_drift
from quantlab.adaptive.ensembles import constrain_weights
from quantlab.adaptive.state import DecayStatus, DriftStatus
from quantlab.core.errors import InfeasibleAdaptiveEnsemble


@pytest.mark.adaptive
def test_stable_ics_are_stable() -> None:
    ics = [0.05 + 0.01 * ((i % 3) - 1) for i in range(40)]
    report = classify_drift(ics, min_obs=16, watch=8.0, detect=20.0)
    assert report.status in {DriftStatus.STABLE, DriftStatus.WATCH}
    assert report.check.value == "pass"


@pytest.mark.adaptive
def test_reversing_ics_can_flag_drift() -> None:
    ics = [0.4] * 20 + [-0.4] * 20
    report = classify_drift(ics, min_obs=16, watch=1.5, detect=3.0)
    assert report.status is DriftStatus.DRIFT_DETECTED
    assert "drift_detected" in report.transitions


@pytest.mark.adaptive
def test_insufficient_decay_is_not_manufactured() -> None:
    estimate = estimate_half_life([0.1, 0.2, 0.15], min_obs=12)
    assert estimate.status is DecayStatus.INSUFFICIENT_DATA
    assert estimate.estimate is None


@pytest.mark.adaptive
def test_decaying_ics_can_be_estimable() -> None:
    ics = [0.4 - 0.01 * i for i in range(30)]
    estimate = estimate_half_life(ics, min_obs=12)
    assert estimate.status in {DecayStatus.ESTIMABLE, DecayStatus.UNSTABLE}
    if estimate.status is DecayStatus.ESTIMABLE:
        assert estimate.estimate is not None
        assert estimate.estimate > 0


@pytest.mark.adaptive
def test_infeasible_ensemble_raises() -> None:
    model = AdaptiveModelDefinition(
        adaptive_model_id="bad",
        version="1",
        name="bad",
        policy=AdaptationPolicy.ENSEMBLE_ADAPTATION,
        learner=LearnerKind.IC_WEIGHTED_ENSEMBLE,
        alpha_ids=["a", "b"],
        min_alpha_weight=0.6,
        max_alpha_weight=0.5,
        min_active_alphas=2,
    )
    with pytest.raises(InfeasibleAdaptiveEnsemble):
        constrain_weights({"a": 0.5, "b": 0.5}, model)


@pytest.mark.adaptive
def test_ensemble_weights_sum_to_one() -> None:
    model = AdaptiveModelDefinition(
        adaptive_model_id="ok",
        version="1",
        name="ok",
        policy=AdaptationPolicy.ENSEMBLE_ADAPTATION,
        learner=LearnerKind.IC_WEIGHTED_ENSEMBLE,
        alpha_ids=["a", "b"],
        min_alpha_weight=0.1,
        max_alpha_weight=0.9,
        max_concentration=0.85,
        min_active_alphas=2,
    )
    weights, fallback = constrain_weights({"a": 0.2, "b": 0.8}, model)
    assert not fallback
    assert sum(weights.values()) == pytest.approx(1.0)
    assert min(weights.values()) >= 0.1 - 1e-12
