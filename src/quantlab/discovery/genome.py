"""Discovery genome. Distinct from domain.research.SignalGenome."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.discovery.definitions import SearchMode
from quantlab.discovery.errors import DiscoveryError
from quantlab.discovery.expression import ExprNode
from quantlab.domain.research import ExpressionNode, SignalGenome


class DiscoveryGenome(BaseModel):
    genome_id: str
    expression: ExprNode
    generation: int = 0
    parents: list[str] = Field(default_factory=list)
    origin: SearchMode = SearchMode.SEEDED
    seed: int = 0
    mutation_ops: list[str] = Field(default_factory=list)

    def identity_hash(self) -> str:
        return self.expression.identity_hash()

    def canonical_text(self) -> str:
        return self.expression.canonical_text()


def to_signal_genome(expr: ExprNode, genome_id: str) -> SignalGenome:
    """Convert a simple tree to Prompt 02 SignalGenome. Rolling ops are not mapped."""
    return SignalGenome(
        genome_id=genome_id,
        inputs=sorted(set(expr.feature_names())),
        expression=_to_domain(expr),
        provenance="discovery_simple_tree",
    )


def _to_domain(expr: ExprNode) -> ExpressionNode:
    if expr.kind.value == "feature":
        return ExpressionNode(op="feature", name=expr.name)
    if expr.op in {"rank", "zscore", "neg", "abs"}:
        return ExpressionNode(op=expr.op, child=_to_domain(expr.children[0]))
    if expr.op in {"add", "sub", "mul", "div", "safe_div"}:
        op = "div" if expr.op == "safe_div" else expr.op
        return ExpressionNode(
            op=op,
            child=_to_domain(expr.children[0]),
            right=_to_domain(expr.children[1]),
        )
    raise DiscoveryError(f"cannot map {expr.op} onto SignalGenome")
