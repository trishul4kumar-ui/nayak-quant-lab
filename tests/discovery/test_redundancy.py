from __future__ import annotations

import pytest

from quantlab.discovery.expression import feature_node, unary
from quantlab.discovery.redundancy import feature_overlap


@pytest.mark.discovery
def test_feature_overlap() -> None:
    a = unary("rank", feature_node("momentum_20"))
    b = feature_node("momentum_20")
    c = feature_node("rolling_std_20")
    assert feature_overlap(a, b) == 1.0
    assert feature_overlap(b, c) == 0.0
