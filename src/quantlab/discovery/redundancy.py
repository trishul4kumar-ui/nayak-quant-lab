"""Structural and output redundancy. Future information is not used."""

from __future__ import annotations

from quantlab.discovery.expression import ExprNode


def feature_overlap(left: ExprNode, right: ExprNode) -> float:
    a = set(left.feature_names())
    b = set(right.feature_names())
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def structural_penalty(expr: ExprNode, peers: list[ExprNode]) -> float:
    if not peers:
        return 0.0
    return max(feature_overlap(expr, peer) for peer in peers)
