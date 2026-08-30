"""Genetic operators. Deterministic under a frozen seed."""

from __future__ import annotations

import random

from quantlab.discovery.crossover import crossover
from quantlab.discovery.definitions import SearchMode
from quantlab.discovery.expression import ExprNode
from quantlab.discovery.mutation import mutate
from quantlab.discovery.population import DiscoveryCandidate
from quantlab.discovery.symbolic import simplify


def tournament(
    members: list[DiscoveryCandidate],
    rng: random.Random,
    k: int = 3,
) -> DiscoveryCandidate:
    picks = [members[rng.randrange(len(members))] for _ in range(max(k, 1))]
    return max(picks, key=lambda item: _scalar(item))


def elite(members: list[DiscoveryCandidate], n: int = 1) -> list[DiscoveryCandidate]:
    ranked = sorted(members, key=lambda item: _scalar(item), reverse=True)
    return ranked[: max(n, 0)]


def breed(
    left: DiscoveryCandidate,
    right: DiscoveryCandidate,
    rng: random.Random,
    grammar: object,
) -> tuple[ExprNode, ExprNode, list[str]]:
    a, b, p1, p2 = crossover(left.expression, right.expression, rng)
    return simplify(a), simplify(b), [p1, p2]


def mutated(expr: ExprNode, rng: random.Random, grammar: object) -> tuple[ExprNode, str]:
    from quantlab.discovery.grammar import GrammarSpec

    spec = grammar if isinstance(grammar, GrammarSpec) else GrammarSpec()
    node, op = mutate(expr, rng, spec)
    return simplify(node), op


def origin_genetic() -> SearchMode:
    return SearchMode.GENETIC


def _scalar(item: DiscoveryCandidate) -> float:
    if item.fitness is None:
        return float("-inf")
    return item.fitness.scalar
