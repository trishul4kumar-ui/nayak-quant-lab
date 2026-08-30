from __future__ import annotations

import pytest

from quantlab.capital.definitions import SizingMethod
from quantlab.capital.library import seed_policy, seed_request
from quantlab.capital.sizing import (
    size_equal_weight,
    size_inverse_vol,
    size_positions,
    size_score_weight,
)

pytestmark = pytest.mark.capital


def test_equal_weight() -> None:
    result = size_equal_weight(["NSE:AAA", "NSE:BBB"], seed_policy())
    assert result.output_weights["NSE:AAA"] == pytest.approx(0.5)
    assert result.method_id == "equal_weight"


def test_score_weight_is_positive_proportional() -> None:
    result = size_score_weight({"NSE:AAA": 2.0, "NSE:BBB": 1.0, "NSE:CCC": -1.0})
    assert result.output_weights["NSE:AAA"] == pytest.approx(2 / 3)
    assert result.output_weights["NSE:CCC"] == pytest.approx(0.0)


def test_inverse_vol() -> None:
    result = size_inverse_vol(["A", "B"], {"A": 0.2, "B": 0.4})
    assert result.output_weights["A"] == pytest.approx(2 / 3)


def test_named_methods_expose_identity() -> None:
    request = seed_request()
    policy = seed_policy().model_copy(update={"sizing_method": SizingMethod.SCORE_WEIGHT})
    result = size_positions(sorted(request.scores), request, policy, confidence=0.5)
    assert result.method_id == "score_weight"
    assert result.input_versions["snapshot"] == "seed"
    assert pytest.approx(sum(result.output_weights.values()), abs=1e-9) == 1.0
