"""Typed expression trees. Distinct from domain.research.ExpressionNode / SignalGenome."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.backtest.spec import config_hash
from quantlab.discovery.definitions import ExprKind, ValueType
from quantlab.discovery.errors import DiscoveryError


class ExprNode(BaseModel):
    kind: ExprKind
    op: str
    name: str = ""
    window: int = 0
    constant: float | None = None
    children: list[ExprNode] = Field(default_factory=list)
    value_type: ValueType = ValueType.PANEL

    def canonical(self) -> ExprNode:
        kids = [c.canonical() for c in self.children]
        if (
            self.op in {"add", "mul", "min", "max"}
            and len(kids) == 2
            and kids[0].canonical_text() > kids[1].canonical_text()
        ):
            kids = [kids[1], kids[0]]
        return self.model_copy(update={"children": kids})

    def canonical_text(self) -> str:
        node = self.canonical()
        if node.kind is ExprKind.FEATURE:
            return node.name
        if node.kind is ExprKind.CONSTANT:
            return str(node.constant)
        if node.window:
            inner = ",".join(c.canonical_text() for c in node.children)
            return f"{node.op}({inner},{node.window})"
        inner = ",".join(c.canonical_text() for c in node.children)
        return f"{node.op}({inner})"

    def identity_hash(self) -> str:
        node = self.canonical()
        return config_hash(
            {
                "kind": node.kind.value,
                "op": node.op,
                "name": node.name,
                "window": node.window,
                "constant": node.constant,
                "children": [c.identity_hash() for c in node.children],
            }
        )

    def depth(self) -> int:
        if not self.children:
            return 1
        return 1 + max(c.depth() for c in self.children)

    def node_count(self) -> int:
        return 1 + sum(c.node_count() for c in self.children)

    def feature_names(self) -> list[str]:
        if self.kind is ExprKind.FEATURE and self.name:
            return [self.name]
        names: list[str] = []
        for child in self.children:
            names.extend(child.feature_names())
        return names

    def uses_forbidden_label(self) -> bool:
        from quantlab.discovery.definitions import FORBIDDEN_PRIMITIVES

        blob = {self.op, self.name}
        if blob & FORBIDDEN_PRIMITIVES:
            return True
        return any(c.uses_forbidden_label() for c in self.children)


def feature_node(name: str) -> ExprNode:
    if not name:
        raise DiscoveryError("feature node requires a registered feature id")
    return ExprNode(kind=ExprKind.FEATURE, op="feature", name=name, value_type=ValueType.PANEL)


def constant_node(value: float) -> ExprNode:
    return ExprNode(kind=ExprKind.CONSTANT, op="const", constant=value, value_type=ValueType.SCALAR)


def unary(op: str, child: ExprNode) -> ExprNode:
    out_type = ValueType.RANKED_CROSS_SECTION if op == "rank" else child.value_type
    return ExprNode(kind=ExprKind.UNARY, op=op, children=[child], value_type=out_type)


def binary(op: str, left: ExprNode, right: ExprNode) -> ExprNode:
    return ExprNode(kind=ExprKind.BINARY, op=op, children=[left, right], value_type=ValueType.PANEL)


def rolling(op: str, child: ExprNode, window: int) -> ExprNode:
    if window < 2:
        raise DiscoveryError("rolling window must be >= 2")
    return ExprNode(
        kind=ExprKind.ROLLING,
        op=op,
        window=window,
        children=[child],
        value_type=ValueType.PANEL,
    )
