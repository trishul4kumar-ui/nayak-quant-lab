from __future__ import annotations

import random

import pytest

from quantlab.discovery.constraints import validate_expression
from quantlab.discovery.generator import seed_expressions
from quantlab.discovery.grammar import GrammarSpec
from quantlab.discovery.mutation import mutate


@pytest.mark.discovery
def test_mutation_stays_typed() -> None:
    grammar = GrammarSpec()
    rng = random.Random(11)
    src = seed_expressions(grammar)[0]
    node, op = mutate(src, rng, grammar)
    validate_expression(node, grammar)
    assert op
