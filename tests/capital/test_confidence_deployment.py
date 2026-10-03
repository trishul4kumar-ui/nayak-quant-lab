from __future__ import annotations

from quantlab.capital.sizing import size_confidence_scaled


def test_confidence_scales_gross_deployment_without_changing_composition() -> None:
    low = size_confidence_scaled({"A": 2.0, "B": 1.0}, 0.3).output_weights
    high = size_confidence_scaled({"A": 2.0, "B": 1.0}, 0.9).output_weights

    assert sum(high.values()) > sum(low.values())
    assert high["A"] / high["B"] == low["A"] / low["B"]
