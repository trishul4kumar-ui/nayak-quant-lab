from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quantlab.discovery.evaluator import evaluate_expression
from quantlab.discovery.expression import feature_node, unary


@pytest.mark.discovery
def test_log_drops_non_positive() -> None:
    ts = datetime(2024, 1, 2, tzinfo=UTC)
    panels = {"momentum_20": {ts: {"A": -1.0, "B": 0.0, "C": 2.0, "D": 4.0}}}
    out = evaluate_expression(unary("log", feature_node("momentum_20")), panels)
    row = out[ts]
    assert "A" not in row
    assert "B" not in row
    assert "C" in row
    assert "D" in row
