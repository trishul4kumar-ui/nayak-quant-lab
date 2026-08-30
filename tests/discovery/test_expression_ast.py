from __future__ import annotations

import pytest

from quantlab.discovery.expression import binary, feature_node, unary


@pytest.mark.discovery
def test_commutative_add_canonical_hash() -> None:
    left = binary("add", feature_node("momentum_5"), feature_node("momentum_20"))
    right = binary("add", feature_node("momentum_20"), feature_node("momentum_5"))
    assert left.canonical_text() == right.canonical_text()
    assert left.identity_hash() == right.identity_hash()


@pytest.mark.discovery
def test_rank_momentum_text() -> None:
    expr = unary("rank", feature_node("momentum_20"))
    assert expr.canonical_text() == "rank(momentum_20)"
    assert expr.feature_names() == ["momentum_20"]
