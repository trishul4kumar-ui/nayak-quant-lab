from datetime import UTC, datetime

from quantlab.alpha.combinations import equal_weight_zscore, residualize, weighted_zscore
from quantlab.alpha.portfolio import evaluate_feature_map, rank_minus_genome
from quantlab.research.genome import evaluate_genome, momentum_genome


def test_equal_weight_zscore_is_explicit() -> None:
    a = {"NSE:A": 1.0, "NSE:B": 2.0, "NSE:C": 3.0}
    b = {"NSE:A": 3.0, "NSE:B": 2.0, "NSE:C": 1.0}
    combined = equal_weight_zscore([a, b])
    assert set(combined) == {"NSE:A", "NSE:B", "NSE:C"}


def test_weighted_zscore_rejects_zero_sum() -> None:
    import pytest

    with pytest.raises(ValueError, match="sum"):
        weighted_zscore([{"a": 1.0, "b": 2.0, "c": 3.0}], [0.0])


def test_residualize_removes_linear_component() -> None:
    x = {"a": 1.0, "b": 2.0, "c": 3.0, "d": 4.0}
    y = {k: 2.0 * v + 1.0 for k, v in x.items()}
    resid = residualize(y, x)
    assert resid is not None
    assert max(abs(v) for v in resid.values()) < 1e-9


def test_rank_minus_genome_evaluates() -> None:
    as_of = datetime(2024, 1, 15, tzinfo=UTC)
    genome = rank_minus_genome("momentum_20", "rolling_std_20")
    feature_map = {
        "momentum_20": {"NSE:AAA": 0.2, "NSE:BBB": -0.1, "NSE:CCC": 0.05},
        "rolling_std_20": {"NSE:AAA": 0.01, "NSE:BBB": 0.04, "NSE:CCC": 0.02},
    }
    signals = evaluate_feature_map(genome, feature_map, as_of)
    assert len(signals) == 3
    existing = evaluate_genome(
        momentum_genome(20),
        {"momentum_20": feature_map["momentum_20"]},
        as_of,
    )
    assert existing[0].instrument.symbol in {"AAA", "BBB", "CCC"}
