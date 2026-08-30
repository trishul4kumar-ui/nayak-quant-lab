"""Expression complexity. Prefer simpler trees when predictive information is comparable."""

from __future__ import annotations

from pydantic import BaseModel

from quantlab.discovery.definitions import ExprKind
from quantlab.discovery.expression import ExprNode


class ComplexityWeights(BaseModel):
    version: str = "1"
    nodes: float = 1.0
    depth: float = 1.5
    operators: float = 1.0
    constants: float = 0.5
    features: float = 1.0


class ComplexityReport(BaseModel):
    node_count: int
    tree_depth: int
    operator_count: int
    feature_count: int
    constant_count: int
    nested_transform_count: int
    lookback_span: int
    score: float
    weights_version: str


def complexity(expr: ExprNode, weights: ComplexityWeights | None = None) -> ComplexityReport:
    w = weights or ComplexityWeights()
    ops = _count_kind(
        expr, {ExprKind.UNARY, ExprKind.BINARY, ExprKind.ROLLING, ExprKind.CROSS_SECTION}
    )
    consts = _count_kind(expr, {ExprKind.CONSTANT})
    nested = max(expr.depth() - 1, 0)
    lookback = _max_window(expr)
    features = len(set(expr.feature_names()))
    score = (
        w.nodes * expr.node_count()
        + w.depth * expr.depth()
        + w.operators * ops
        + w.constants * consts
        + w.features * features
    )
    return ComplexityReport(
        node_count=expr.node_count(),
        tree_depth=expr.depth(),
        operator_count=ops,
        feature_count=features,
        constant_count=consts,
        nested_transform_count=nested,
        lookback_span=lookback,
        score=score,
        weights_version=w.version,
    )


def _count_kind(expr: ExprNode, kinds: set[ExprKind]) -> int:
    n = 1 if expr.kind in kinds else 0
    return n + sum(_count_kind(c, kinds) for c in expr.children)


def _max_window(expr: ExprNode) -> int:
    return max([expr.window, *(_max_window(c) for c in expr.children)], default=0)
