from __future__ import annotations

import random

import pytest

from quantlab.discovery.constraints import validate_expression
from quantlab.discovery.crossover import crossover
from quantlab.discovery.generator import seed_expressions
from quantlab.discovery.grammar import GrammarSpec


@pytest.mark.discovery
def test_crossover_records_parents() -> None:
    grammar = GrammarSpec()
    seeds = seed_expressions(grammar)
    child_a, child_b, p1, p2 = crossover(seeds[0], seeds[1], random.Random(3))
    validate_expression(child_a, grammar)
    validate_expression(child_b, grammar)
    assert p1 == seeds[0].identity_hash()
    assert p2 == seeds[1].identity_hash()
