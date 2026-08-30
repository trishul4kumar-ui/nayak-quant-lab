"""Candidate generation. Labels are never primitives."""

from __future__ import annotations

import random

from quantlab.discovery.definitions import ExprKind, SearchMode
from quantlab.discovery.errors import DiscoveryError
from quantlab.discovery.expression import (
    ExprNode,
    binary,
    constant_node,
    feature_node,
    rolling,
    unary,
)
from quantlab.discovery.grammar import GrammarSpec
from quantlab.discovery.primitives import assert_not_label


def random_expression(rng: random.Random, grammar: GrammarSpec, depth: int = 0) -> ExprNode:
    if depth >= grammar.max_depth - 1 or rng.random() < 0.35:
        name = rng.choice(list(grammar.allowed_features))
        assert_not_label(name)
        return feature_node(name)
    choice = rng.choice(["unary", "cs", "binary", "rolling", "feature"])
    if choice == "feature":
        return feature_node(rng.choice(list(grammar.allowed_features)))
    child = random_expression(rng, grammar, depth + 1)
    if choice == "unary":
        return unary(rng.choice(list(grammar.allowed_unary[:3])), child)
    if choice == "cs":
        return unary(rng.choice(("rank", "zscore", "demean")), child)
    if choice == "rolling":
        return rolling(
            rng.choice(list(grammar.allowed_rolling)),
            child,
            rng.choice(list(grammar.allowed_windows)),
        )
    right = random_expression(rng, grammar, depth + 1)
    if rng.random() < 0.15 and depth > 0:
        right = constant_node(rng.choice((1.0, 2.0, -1.0)))
    return binary(rng.choice(list(grammar.allowed_binary)), child, right)


def seed_expressions(grammar: GrammarSpec | None = None) -> list[ExprNode]:
    spec = grammar or GrammarSpec()
    feats = list(spec.allowed_features)
    if "momentum_20" not in feats:
        raise DiscoveryError("seed grammar missing momentum_20")
    mom20 = feature_node("momentum_20")
    seeds = [
        mom20,
        unary("rank", mom20),
        unary("zscore", mom20),
    ]
    if "rolling_std_20" in feats:
        vol = feature_node("rolling_std_20")
        seeds.append(unary("rank", binary("safe_div", mom20, vol)))
        seeds.append(unary("rank", binary("sub", mom20, vol)))
    if "momentum_5" in feats and "rolling_std_20" in feats:
        seeds.append(
            unary(
                "rank",
                binary("sub", feature_node("momentum_5"), feature_node("rolling_std_20")),
            )
        )
    for node in seeds:
        for name in node.feature_names():
            assert_not_label(name)
    return seeds


def human_hypothesis(text: str, grammar: GrammarSpec | None = None) -> ExprNode:
    """Parse a tiny prefix form: rank(momentum_20). Not a general language."""
    spec = grammar or GrammarSpec()
    stripped = text.strip().replace(" ", "")
    for feat in spec.allowed_features:
        if stripped == feat:
            return feature_node(feat)
    if stripped.startswith("rank(") and stripped.endswith(")"):
        inner = stripped[5:-1]
        return unary("rank", human_hypothesis(inner, spec))
    if stripped.startswith("zscore(") and stripped.endswith(")"):
        inner = stripped[7:-1]
        return unary("zscore", human_hypothesis(inner, spec))
    raise DiscoveryError(f"unsupported human hypothesis: {text}")


def collect_nodes(expr: ExprNode) -> list[ExprNode]:
    out = [expr]
    for child in expr.children:
        out.extend(collect_nodes(child))
    return out


def replace_child(root: ExprNode, target: ExprNode, replacement: ExprNode) -> ExprNode:
    same = root is target or (
        root.identity_hash() == target.identity_hash() and root.op == target.op
    )
    if same and root.kind is target.kind:
        return replacement
    kids = [replace_child(child, target, replacement) for child in root.children]
    return root.model_copy(update={"children": kids})


def node_kind_ok(kind: ExprKind) -> bool:
    return kind in {
        ExprKind.FEATURE,
        ExprKind.CONSTANT,
        ExprKind.UNARY,
        ExprKind.BINARY,
        ExprKind.ROLLING,
        ExprKind.CROSS_SECTION,
    }


def generation_mode() -> SearchMode:
    return SearchMode.RANDOM
