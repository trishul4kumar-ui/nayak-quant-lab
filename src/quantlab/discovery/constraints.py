"""Grammar and type constraints. Invalid trees fail closed."""

from __future__ import annotations

from quantlab.discovery.definitions import ExprKind
from quantlab.discovery.errors import DiscoveryError
from quantlab.discovery.expression import ExprNode
from quantlab.discovery.grammar import GrammarSpec
from quantlab.discovery.operators import CS_OPS, OPERATORS
from quantlab.discovery.primitives import assert_not_label


def validate_expression(expr: ExprNode, grammar: GrammarSpec | None = None) -> None:
    spec = grammar or GrammarSpec()
    if expr.uses_forbidden_label():
        raise DiscoveryError("label entered a discovery expression")
    if expr.depth() > spec.max_depth:
        raise DiscoveryError(f"depth {expr.depth()} exceeds max_depth {spec.max_depth}")
    if expr.node_count() > spec.max_nodes:
        raise DiscoveryError(f"nodes {expr.node_count()} exceed max_nodes {spec.max_nodes}")
    features = set(expr.feature_names())
    if len(features) > spec.max_features:
        raise DiscoveryError("too many features")
    unknown = features - set(spec.allowed_features)
    if unknown:
        raise DiscoveryError(f"feature not in grammar: {sorted(unknown)}")
    constants = _count_constants(expr)
    if constants > spec.max_constants:
        raise DiscoveryError("too many constants")
    _walk(expr, spec)


def _count_constants(expr: ExprNode) -> int:
    n = 1 if expr.kind is ExprKind.CONSTANT else 0
    return n + sum(_count_constants(child) for child in expr.children)


def _walk(expr: ExprNode, spec: GrammarSpec) -> None:
    if expr.kind is ExprKind.FEATURE:
        assert_not_label(expr.name)
        return
    if expr.kind is ExprKind.CONSTANT:
        return
    op = OPERATORS.get(expr.op)
    if op is None:
        raise DiscoveryError(f"unknown operator {expr.op}")
    if op.arity == 1 and len(expr.children) != 1:
        raise DiscoveryError(f"operator {expr.op} requires one child")
    if op.arity == 2 and len(expr.children) != 2:
        raise DiscoveryError(f"binary {expr.op} requires two children")
    if expr.kind is ExprKind.ROLLING and expr.window not in spec.allowed_windows:
        raise DiscoveryError(f"window {expr.window} not in grammar")
    if expr.op in CS_OPS and expr.children[0].kind is ExprKind.CONSTANT:
        raise DiscoveryError("cross-section operator requires a panel child")
    for child in expr.children:
        _walk(child, spec)
