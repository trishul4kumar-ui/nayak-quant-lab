from __future__ import annotations

import pytest

from quantlab.capital.allocator import allocate
from quantlab.capital.diagnostics import stability_l1
from quantlab.capital.library import seed_request

pytestmark = pytest.mark.capital


def test_small_score_perturbation_is_measurable() -> None:
    base = allocate(seed_request())
    scores = dict(seed_request().scores)
    name = sorted(scores)[0]
    scores[name] += 1e-6
    perturbed = allocate(seed_request(scores=scores))
    delta = stability_l1(base.decision.target_weights, perturbed.decision.target_weights)
    assert delta >= 0.0
