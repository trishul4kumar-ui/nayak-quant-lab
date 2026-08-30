from __future__ import annotations

from quantlab.execution_research.impact import impact_bps
from quantlab.execution_research.registry import get_execution_model


def test_square_root_impact_is_uncalibrated_and_increases_with_size() -> None:
    model = get_execution_model("exec_high_impact")
    small, status, check, note = impact_bps(
        model, quantity=1_000.0, volume=1_000_000.0, trailing_vol=0.01
    )
    large, _, _, _ = impact_bps(model, quantity=100_000.0, volume=1_000_000.0, trailing_vol=0.01)
    assert small is not None and large is not None
    assert large > small
    assert status.value == "uncalibrated"
    assert check.value == "warn"
    assert "UNCALIBRATED" in note


def test_missing_volume_does_not_become_zero_impact() -> None:
    model = get_execution_model("exec_high_impact")
    value, status, check, _note = impact_bps(
        model, quantity=1_000.0, volume=None, trailing_vol=0.01
    )
    assert value is None
    assert status.value == "not_tested"
    assert check.value == "not_tested"
