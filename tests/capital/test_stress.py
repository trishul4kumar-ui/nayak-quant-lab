from __future__ import annotations

import pytest

from quantlab.capital.diagnostics import stress_allocation
from quantlab.capital.library import seed_covariance, seed_request
from quantlab.risk.stress import StressScenario

pytestmark = pytest.mark.capital


def test_stress_reuses_prompt_08() -> None:
    request = seed_request()
    result = stress_allocation(
        {"NSE:AAA": 0.4, "NSE:BBB": 0.3, "NSE:CCC": 0.3},
        seed_covariance(),
        StressScenario(scenario_id="vol_up", kind="vol_shock", description="vol up", vol_shock=0.5),
    )
    assert result.scenario_id == "vol_up"
    assert result.stressed_variance is not None
    assert "forecast" in result.note
    assert request.as_of
