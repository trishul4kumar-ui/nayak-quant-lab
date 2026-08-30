"""Typed mutations. Future information does not enter mutation."""

from __future__ import annotations

import random

from quantlab.discovery.expression import ExprNode, feature_node, unary
from quantlab.discovery.generator import collect_nodes, random_expression
from quantlab.discovery.grammar import GrammarSpec


def mutate(expr: ExprNode, rng: random.Random, grammar: GrammarSpec) -> tuple[ExprNode, str]:
    nodes = collect_nodes(expr)
    target = rng.choice(nodes)
    op = rng.choice(("feature", "operator", "window", "subtree"))
    if op == "feature" and target.kind.value == "feature":
        name = rng.choice(list(grammar.allowed_features))
        return _swap(expr, target, feature_node(name)), "replace_feature"
    if op == "operator" and target.kind.value in {"unary", "cross_section"}:
        new_op = rng.choice(list(grammar.allowed_unary))
        child = target.children[0] if target.children else random_expression(rng, grammar)
        return _swap(expr, target, unary(new_op, child)), "replace_operator"
    if op == "window" and target.kind.value == "rolling":
        updated = target.model_copy(update={"window": rng.choice(list(grammar.allowed_windows))})
        return _swap(expr, target, updated), "replace_window"
    replacement = random_expression(rng, grammar, depth=max(target.depth() - 1, 0))
    return _swap(expr, target, replacement), "replace_subtree"


def _swap(root: ExprNode, target: ExprNode, replacement: ExprNode) -> ExprNode:
    if id(root) == id(target) or (
        root.kind == target.kind
        and root.op == target.op
        and root.name == target.name
        and root.window == target.window
        and root.constant == target.constant
        and len(root.children) == len(target.children)
        and root.canonical_text() == target.canonical_text()
    ):
        return replacement
    kids = [_swap(child, target, replacement) for child in root.children]
    return root.model_copy(update={"children": kids})
