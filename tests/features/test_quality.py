from quantlab.features.cache import feature_cache_key
from quantlab.features.correlation import correlate_panels
from quantlab.features.engine import Panel
from quantlab.features.quality import summarize_quality
from quantlab.features.registry import get_feature


def _panel() -> Panel:
    from datetime import UTC, datetime

    t0 = datetime(2024, 1, 2, tzinfo=UTC)
    t1 = datetime(2024, 1, 3, tzinfo=UTC)
    return {
        t0: {"NSE:A": 1.0, "NSE:B": 2.0, "NSE:C": 3.0},
        t1: {"NSE:A": 1.5, "NSE:B": 2.5, "NSE:C": 3.5},
    }


def test_quality_reports_coverage() -> None:
    report = summarize_quality(_panel(), expected_names=3)
    assert report.n == 6
    assert report.coverage == 1.0
    assert report.unique == 6
    assert report.mean is not None


def test_identical_panels_are_redundant() -> None:
    panel = _panel()
    pair = correlate_panels("a", panel, "b", panel)
    assert pair.redundant
    assert pair.spearman is not None
    assert pair.spearman > 0.99


def test_independent_noise_is_not_redundant() -> None:
    from datetime import UTC, datetime

    t0 = datetime(2024, 1, 2, tzinfo=UTC)
    left = {t0: {"NSE:A": 1.0, "NSE:B": 2.0, "NSE:C": 3.0, "NSE:D": 4.0}}
    right = {t0: {"NSE:A": 4.0, "NSE:B": 1.0, "NSE:C": 5.0, "NSE:D": 0.0}}
    pair = correlate_panels("a", left, "b", right, redundant_threshold=0.9)
    assert not pair.redundant


def test_cache_key_includes_snapshot_and_version() -> None:
    feature = get_feature("momentum_20")
    a = feature_cache_key(
        feature,
        snapshot_id="s1",
        universe=["NSE:TCS"],
        start=None,
        end=None,
        frequency="1d",
        normalization="none",
    )
    b = feature_cache_key(
        feature,
        snapshot_id="s2",
        universe=["NSE:TCS"],
        start=None,
        end=None,
        frequency="1d",
        normalization="none",
    )
    assert a != b
    changed = feature.model_copy(update={"version": "9"})
    c = feature_cache_key(
        changed,
        snapshot_id="s1",
        universe=["NSE:TCS"],
        start=None,
        end=None,
        frequency="1d",
        normalization="none",
    )
    assert a != c
