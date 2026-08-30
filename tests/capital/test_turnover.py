from __future__ import annotations

import pytest

from quantlab.capital.turnover import estimate_turnover
from quantlab.portfolio.turnover import two_sided_turnover

pytestmark = pytest.mark.capital


def test_turnover_matches_prompt_07_convention() -> None:
    prev = {"A": 0.5, "B": 0.5}
    new = {"A": 1.0}
    assert estimate_turnover(prev, new) == pytest.approx(two_sided_turnover(prev, new))
    assert estimate_turnover(prev, new) == pytest.approx(0.5)
