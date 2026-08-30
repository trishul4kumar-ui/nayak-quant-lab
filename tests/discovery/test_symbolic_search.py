from __future__ import annotations

import pytest

from quantlab.discovery.expression import binary, constant_node, feature_node
from quantlab.discovery.symbolic import simplify


@pytest.mark.discovery
def test_simplify_mul_one() -> None:
    expr = binary("mul", feature_node("momentum_20"), feature_node("momentum_5"))
    node = binary("mul", feature_node("momentum_5"), constant_node(1.0))
    assert simplify(node).canonical_text() == "momentum_5"
    assert simplify(expr).op == "mul"
