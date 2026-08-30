"""Conservative simplification. Domain and availability are preserved."""

from __future__ import annotations

from quantlab.discovery.definitions import ExprKind
from quantlab.discovery.expression import ExprNode


def simplify(expr: ExprNode) -> ExprNode:
    kids = [simplify(child) for child in expr.children]
    node = expr.model_copy(update={"children": kids}).canonical()
    if node.op == "add" and len(kids) == 2:
        if _is_const(kids[0], 0.0):
            return kids[1]
        if _is_const(kids[1], 0.0):
            return kids[0]
    if node.op == "mul" and len(kids) == 2:
        if _is_const(kids[0], 1.0):
            return kids[1]
        if _is_const(kids[1], 1.0):
            return kids[0]
    if node.op == "rank" and kids and kids[0].op == "rank":
        return kids[0]
    return node


def _is_const(node: ExprNode, value: float) -> bool:
    return node.kind is ExprKind.CONSTANT and node.constant is not None and node.constant == value
