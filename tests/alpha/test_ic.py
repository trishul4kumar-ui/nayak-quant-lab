from datetime import UTC, datetime

import pytest

from quantlab.alpha.ic import information_coefficient
from quantlab.alpha.quantiles import assign_quantiles, quantile_analysis
from quantlab.alpha.synthetics import leaky_forward_panel, permute_panel
from quantlab.domain.research import CheckResult
from quantlab.features.engine import Panel


def _dates() -> list[datetime]:
    return [datetime(2024, 1, d, tzinfo=UTC) for d in range(2, 22)]


def _known_signal() -> tuple[Panel, Panel]:
    dates = _dates()
    names = [f"NSE:A{i}" for i in range(8)]
    scores = {name: float(i) for i, name in enumerate(names)}
    feature = {day: dict(scores) for day in dates}
    label = {
        day: {name: 0.1 * scores[name] + 0.02 * ((d + i) % 5) / 5.0 for i, name in enumerate(names)}
        for d, day in enumerate(dates)
    }
    return feature, label


def test_ic_detects_known_correlation() -> None:
    feature, label = _known_signal()
    report = information_coefficient(feature, label, min_sample=8)
    assert report.status is CheckResult.PASS
    assert report.spearman_mean is not None
    assert report.spearman_mean > 0.9
    assert report.n >= 8
    if report.std not in {None, 0.0}:
        assert report.t_stat is not None


def test_ic_small_sample_is_not_tested() -> None:
    day = datetime(2024, 1, 2, tzinfo=UTC)
    feature = {day: {"NSE:A": 1.0, "NSE:B": 2.0, "NSE:C": 3.0}}
    label = {day: {"NSE:A": 0.1, "NSE:B": 0.2, "NSE:C": 0.3}}
    report = information_coefficient(feature, label, min_sample=8)
    assert report.status is CheckResult.NOT_TESTED
    assert report.t_stat is None


def test_null_permuted_feature_is_not_systematically_strong() -> None:
    feature, label = _known_signal()
    shuffled = permute_panel(feature, seed=7)
    report = information_coefficient(shuffled, label, min_sample=8)
    assert report.spearman_mean is not None
    assert abs(report.spearman_mean) < 0.5


def test_quantile_assignment_and_spread() -> None:
    feature, label = _known_signal()
    assigned = assign_quantiles(feature[next(iter(feature))])
    assert set(assigned.values()) <= {1, 2, 3, 4, 5}
    report = quantile_analysis(feature, label)
    assert report.long_short_spread is not None
    assert report.long_short_spread > 0
    assert report.monotonicity is not None
    assert report.monotonicity == pytest.approx(1.0)


def test_leaky_panel_equals_label() -> None:
    _, label = _known_signal()
    leaky = leaky_forward_panel(label)
    assert leaky == label
