from quantlab.features.definition import NormalizationMethod
from quantlab.features.normalize import apply_cross_section, percentile_ranks, robust_zscore
from quantlab.math.metrics import cross_sectional_ranks, zscore


def test_rank_ties_share_average() -> None:
    ranks = cross_sectional_ranks({"a": 1.0, "b": 1.0, "c": 2.0})
    assert ranks["a"] == ranks["b"]
    assert ranks["c"] > ranks["a"]


def test_percentile_ranks_scale_to_100() -> None:
    pct = percentile_ranks({"a": 1.0, "b": 2.0, "c": 3.0})
    assert pct["a"] == 0.0
    assert pct["c"] == 100.0


def test_cs_zscore_matches_primitive() -> None:
    values = {"a": 1.0, "b": 2.0, "c": 3.0}
    got = apply_cross_section(values, NormalizationMethod.ZSCORE_CS)
    expected = zscore([1.0, 2.0, 3.0])
    assert list(got.values()) == expected


def test_robust_zscore_zero_mad() -> None:
    assert robust_zscore({"a": 2.0, "b": 2.0, "c": 2.0}) == {"a": 0.0, "b": 0.0, "c": 0.0}
