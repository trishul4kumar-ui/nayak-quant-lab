from __future__ import annotations

import pytest

from quantlab.discovery.constraints import validate_expression
from quantlab.discovery.errors import DiscoveryError
from quantlab.discovery.expression import feature_node, unary
from quantlab.discovery.grammar import GrammarSpec
from quantlab.discovery.primitives import assert_not_label


@pytest.mark.discovery
def test_grammar_rejects_label_and_depth() -> None:
    with pytest.raises(DiscoveryError):
        assert_not_label("forward_return")
    deep = feature_node("momentum_20")
    for _ in range(6):
        deep = unary("abs", deep)
    with pytest.raises(DiscoveryError, match="depth"):
        validate_expression(deep, GrammarSpec(max_depth=4))
