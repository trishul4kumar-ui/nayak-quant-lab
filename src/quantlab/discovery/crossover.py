"""Type-compatible subtree crossover. Both parents are recorded."""

from __future__ import annotations

import random

from quantlab.discovery.expression import ExprNode
from quantlab.discovery.generator import collect_nodes
from quantlab.discovery.mutation import _swap


def crossover(
    left: ExprNode,
    right: ExprNode,
    rng: random.Random,
) -> tuple[ExprNode, ExprNode, str, str]:
    left_nodes = collect_nodes(left)
    right_nodes = collect_nodes(right)
    a = rng.choice(left_nodes)
    compatible = [n for n in right_nodes if n.value_type == a.value_type]
    if not compatible:
        compatible = right_nodes
    b = rng.choice(compatible)
    child_a = _swap(left, a, b)
    child_b = _swap(right, b, a)
    return child_a, child_b, left.identity_hash(), right.identity_hash()
