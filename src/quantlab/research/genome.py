"""Evaluate a SignalGenome AST over a cross-section of feature values."""

from __future__ import annotations

from datetime import datetime

from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import Signal
from quantlab.domain.research import ExpressionNode, SignalGenome
from quantlab.math.metrics import cross_sectional_ranks, zscore


def evaluate_genome(
    genome: SignalGenome,
    feature_map: dict[str, dict[str, float]],
    as_of: datetime,
) -> list[Signal]:
    """feature_map: feature_name -> {instrument_str: value}."""
    values = _eval_node(genome.expression, feature_map)
    signals: list[Signal] = []
    for inst_key, score in values.items():
        signals.append(Signal(instrument=InstrumentId.parse(inst_key), score=score, as_of=as_of))
    return signals


def _eval_node(
    node: ExpressionNode,
    feature_map: dict[str, dict[str, float]],
) -> dict[str, float]:
    op = node.op.lower()
    if op == "feature":
        if not node.name:
            raise ValueError("feature node requires name")
        return dict(feature_map.get(node.name, {}))
    if op in {"add", "sub"}:
        if node.child is None or node.right is None:
            raise ValueError(f"operator {op} requires child and right")
        left = _eval_node(node.child, feature_map)
        right = _eval_node(node.right, feature_map)
        keys = set(left) & set(right)
        if op == "add":
            return {k: left[k] + right[k] for k in keys}
        return {k: left[k] - right[k] for k in keys}
    if node.child is None:
        raise ValueError(f"operator {op} requires a child")
    if op == "scale":
        weight = 1.0 if node.weight is None else node.weight
        inner = _eval_node(node.child, feature_map)
        return {k: weight * v for k, v in inner.items()}
    inner = _eval_node(node.child, feature_map)
    if op == "zscore":
        names = list(inner.keys())
        scaled = zscore([inner[k] for k in names])
        return {names[i]: scaled[i] for i in range(len(names))}
    if op == "rank":
        return cross_sectional_ranks(inner)
    if op == "identity":
        return inner
    raise ValueError(f"unsupported genome op: {op}")


def momentum_genome(lookback: int) -> SignalGenome:
    feature = f"momentum_{lookback}"
    return SignalGenome(
        genome_id=f"rank_zscore_{feature}",
        version="0.1.0",
        inputs=[feature],
        expression=ExpressionNode(
            op="rank",
            child=ExpressionNode(op="zscore", child=ExpressionNode(op="feature", name=feature)),
        ),
        provenance="prompt02-cs-momentum",
    )
