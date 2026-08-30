"""EWMA weights: newest age=0, half-life maps to weight 0.5."""

from __future__ import annotations

import pytest

from quantlab.adaptive.ewma import decay_lambda, effective_sample_size, ewma_mean, ewma_weights
from quantlab.core.errors import AdaptiveError


@pytest.mark.adaptive
def test_half_life_weight_is_one_half() -> None:
    half = 10.0
    weights = ewma_weights(11, half)
    assert weights[-1] == pytest.approx(1.0)
    assert weights[0] == pytest.approx(0.5)
    assert decay_lambda(half) ** 10 == pytest.approx(0.5)


@pytest.mark.adaptive
def test_ess_is_between_one_and_n() -> None:
    weights = ewma_weights(20, 5.0)
    ess = effective_sample_size(weights)
    assert 1.0 < ess < 20.0


@pytest.mark.adaptive
def test_ewma_mean_prefers_recent() -> None:
    values = [0.0] * 20 + [1.0]
    assert ewma_mean(values, 3.0) > ewma_mean(values, 30.0)


@pytest.mark.adaptive
def test_nonpositive_half_life_fails() -> None:
    with pytest.raises(AdaptiveError):
        decay_lambda(0.0)
