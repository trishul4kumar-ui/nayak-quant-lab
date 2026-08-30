from __future__ import annotations

import pytest

from quantlab.discovery.complexity import complexity
from quantlab.discovery.expression import binary, constant_node, feature_node, unary
from quantlab.discovery.symbolic import simplify


@pytest.mark.discovery
def test_simpler_tree_has_lower_complexity() -> None:
    simple = unary("rank", feature_node("momentum_20"))
    nested = unary("rank", unary("abs", unary("zscore", feature_node("momentum_20"))))
    assert complexity(simple).score < complexity(nested).score


@pytest.mark.discovery
def test_simplify_drops_add_zero() -> None:
    expr = binary("add", feature_node("momentum_20"), constant_node(0.0))
    assert simplify(expr).canonical_text() == "momentum_20"
