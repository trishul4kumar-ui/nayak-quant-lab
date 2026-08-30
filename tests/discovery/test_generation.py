from __future__ import annotations

import random

import pytest

from quantlab.discovery.constraints import validate_expression
from quantlab.discovery.errors import DiscoveryError
from quantlab.discovery.generator import human_hypothesis, random_expression, seed_expressions
from quantlab.discovery.grammar import GrammarSpec
from quantlab.discovery.primitives import FORBIDDEN_PRIMITIVES


@pytest.mark.discovery
def test_seeds_and_random_stay_in_grammar() -> None:
    grammar = GrammarSpec()
    rng = random.Random(7)
    for expr in [*seed_expressions(grammar), random_expression(rng, grammar)]:
        validate_expression(expr, grammar)
        for name in expr.feature_names():
            assert name not in FORBIDDEN_PRIMITIVES
    parsed = human_hypothesis("rank(momentum_20)", grammar)
    assert parsed.canonical_text() == "rank(momentum_20)"
    with pytest.raises(DiscoveryError):
        human_hypothesis("rank(forward_return)", grammar)
