"""Map an alpha panel to Signal objects for the existing genome/backtest path."""

from __future__ import annotations

from datetime import datetime

from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import Signal
from quantlab.domain.research import ExpressionNode, SignalGenome
from quantlab.features.engine import Panel
from quantlab.math.metrics import cross_sectional_ranks, zscore
from quantlab.research.genome import evaluate_genome


def panel_to_signals(
    panel_row: dict[str, float],
    as_of: datetime,
    transform: str = "rank",
) -> list[Signal]:
    if transform == "rank":
        scores = cross_sectional_ranks(panel_row)
    elif transform == "zscore":
        keys = list(panel_row.keys())
        scaled = zscore([panel_row[k] for k in keys])
        scores = {keys[i]: scaled[i] for i in range(len(keys))}
    else:
        scores = dict(panel_row)
    return [
        Signal(instrument=InstrumentId.parse(key), score=value, as_of=as_of)
        for key, value in scores.items()
    ]


def panel_to_signal_map(panel: Panel, transform: str = "rank") -> dict[datetime, list[Signal]]:
    return {as_of: panel_to_signals(row, as_of, transform) for as_of, row in panel.items()}


def rank_minus_genome(left_feature: str, right_feature: str) -> SignalGenome:
    """rank(zscore(left) - zscore(right)). Extends the AST; no Python eval."""
    return SignalGenome(
        genome_id=f"rank_sub_{left_feature}_{right_feature}",
        version="0.6.0",
        inputs=[left_feature, right_feature],
        expression=ExpressionNode(
            op="rank",
            child=ExpressionNode(
                op="sub",
                child=ExpressionNode(
                    op="zscore",
                    child=ExpressionNode(op="feature", name=left_feature),
                ),
                right=ExpressionNode(
                    op="zscore",
                    child=ExpressionNode(op="feature", name=right_feature),
                ),
            ),
        ),
        provenance="prompt06-alpha-combination",
    )


def evaluate_feature_map(
    genome: SignalGenome,
    feature_map: dict[str, dict[str, float]],
    as_of: datetime,
) -> list[Signal]:
    return evaluate_genome(genome, feature_map, as_of)
