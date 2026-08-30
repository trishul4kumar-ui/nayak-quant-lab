from __future__ import annotations

import pytest

from quantlab.capital.library import seed_covariance, seed_request
from quantlab.capital.optimizer import erc_weights, mean_variance_weights

pytestmark = pytest.mark.capital


def test_mean_variance_reuses_existing_optimizer() -> None:
    request = seed_request()
    names = list(request.covariance.names)  # type: ignore[union-attr]
    weights = mean_variance_weights(names, request.scores, seed_covariance(), 1.0)
    assert pytest.approx(sum(weights.values()), abs=1e-8) == 1.0


def test_erc_reuses_existing_optimizer() -> None:
    names = list(seed_covariance().names)
    weights = erc_weights(names, seed_covariance())
    assert all(w >= -1e-12 for w in weights.values())
    assert pytest.approx(sum(weights.values()), abs=1e-8) == 1.0
