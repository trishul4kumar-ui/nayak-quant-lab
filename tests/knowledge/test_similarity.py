from __future__ import annotations

import pytest

from quantlab.discovery.expression import binary, feature_node, unary
from quantlab.knowledge.entities import SimilarityClass
from quantlab.knowledge.similarity import expression_similarity, novelty_hint

pytestmark = pytest.mark.knowledge


def test_commutative_add_is_identical() -> None:
    left = binary("add", feature_node("momentum_5"), feature_node("momentum_10"))
    right = binary("add", feature_node("momentum_10"), feature_node("momentum_5"))
    assert left.identity_hash() == right.identity_hash()
    assert expression_similarity(left, right) is SimilarityClass.IDENTICAL


def test_related_vs_distinct() -> None:
    mom = unary("rank", feature_node("momentum_20"))
    vol = unary("rank", feature_node("rolling_std_20"))
    both = unary(
        "rank", binary("safe_div", feature_node("momentum_20"), feature_node("rolling_std_20"))
    )
    assert expression_similarity(mom, vol) is SimilarityClass.DISTINCT
    assert expression_similarity(mom, both) is SimilarityClass.RELATED
    assert novelty_hint(mom, [mom]).value == "known"
    assert novelty_hint(vol, [mom]).value == "novel"
