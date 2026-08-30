from datetime import UTC, datetime

from quantlab.domain.research import ExpressionNode
from quantlab.research.genome import evaluate_genome, momentum_genome


def test_momentum_genome_ranks_high_momentum_higher() -> None:
    as_of = datetime(2024, 1, 15, tzinfo=UTC)
    genome = momentum_genome(20)
    feature_map = {
        "momentum_20": {
            "NSE:AAA": 0.2,
            "NSE:BBB": -0.1,
            "NSE:CCC": 0.05,
        }
    }
    signals = evaluate_genome(genome, feature_map, as_of)
    ranked = sorted(signals, key=lambda s: s.score, reverse=True)
    assert ranked[0].instrument.symbol == "AAA"
    assert ranked[-1].instrument.symbol == "BBB"


def test_sub_genome_keeps_existing_rank_zscore() -> None:
    as_of = datetime(2024, 1, 15, tzinfo=UTC)
    genome = momentum_genome(20)
    assert genome.expression.right is None
    feature_map = {
        "momentum_20": {"NSE:AAA": 1.0, "NSE:BBB": 0.0, "NSE:CCC": -1.0},
        "vol": {"NSE:AAA": 0.1, "NSE:BBB": 0.1, "NSE:CCC": 0.1},
    }
    node = ExpressionNode(
        op="sub",
        child=ExpressionNode(op="feature", name="momentum_20"),
        right=ExpressionNode(op="feature", name="vol"),
    )
    from quantlab.domain.research import SignalGenome

    combo = SignalGenome(genome_id="sub", inputs=["momentum_20", "vol"], expression=node)
    signals = evaluate_genome(combo, feature_map, as_of)
    ranked = sorted(signals, key=lambda s: s.score, reverse=True)
    assert ranked[0].instrument.symbol == "AAA"
    assert evaluate_genome(genome, {"momentum_20": feature_map["momentum_20"]}, as_of)
