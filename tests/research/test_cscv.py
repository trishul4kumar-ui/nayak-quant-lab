from datetime import UTC, datetime, timedelta

import pytest

from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.domain.research import CheckResult
from quantlab.research.multiple_testing import (
    cscv_overfitting,
    probability_of_backtest_overfitting,
)
from quantlab.research.suite import ValidationConfig, _family_cscv, run_validation_suite


def test_cscv_detects_stable_winner_without_claiming_promotion() -> None:
    report = cscv_overfitting([[0.0] * 8, [0.01] * 8], n_blocks=4)
    assert report.pbo == 0.0
    assert report.n_splits == 6
    assert len(report.logits) == 6
    assert report.status is CheckResult.WARN


def test_cscv_selects_in_sample_and_ranks_out_of_sample() -> None:
    trial = [v for v in (1.0, 2.0, 3.0, -10.0) for _ in range(2)]
    report = cscv_overfitting([trial, [-v for v in trial]], n_blocks=4)
    assert report.pbo == 1.0
    assert all(value < 0 for value in report.logits)


@pytest.mark.parametrize(
    ("trials", "blocks"),
    [
        ([[0.0] * 8], 4),
        ([[0.0] * 8, [0.0] * 7], 4),
        ([[0.0] * 8, [float("nan")] * 8], 4),
        ([[0.0] * 8, [1.0] * 8], 3),
        ([[0.0] * 8, [1.0] * 8], 18),
        ([[0.0] * 7, [1.0] * 7], 4),
        ([[0.0] * 8, [0.0] * 8], 4),
    ],
)
def test_cscv_rejects_inadequate_or_ambiguous_data(
    trials: list[list[float]], blocks: int
) -> None:
    report = cscv_overfitting(trials, n_blocks=blocks)
    assert report.status is CheckResult.NOT_TESTED
    assert report.pbo is None


def test_aggregate_proxy_is_not_mislabelled_as_cscv() -> None:
    report = probability_of_backtest_overfitting([1.0] * 8, [-1.0] * 8)
    assert report.status is CheckResult.NOT_TESTED
    assert report.pbo is None


def test_family_alignment_rejects_missing_dates() -> None:
    start = datetime(2024, 1, 1, tzinfo=UTC)
    dates = [start + timedelta(days=i) for i in range(9)]
    report = _family_cscv(
        [(dates[1:], [0.0] * 8), (dates[:-1], [0.1] * 8)], n_blocks=4
    )
    assert report.status is CheckResult.NOT_TESTED
    assert "dates" in report.note


def test_family_alignment_accepts_only_common_complete_suffix() -> None:
    start = datetime(2024, 1, 1, tzinfo=UTC)
    dates = [start + timedelta(days=i) for i in range(9)]
    report = _family_cscv(
        [(dates, [0.0] * 9), (dates[1:], [0.1] * 8)], n_blocks=4
    )
    assert report.status is CheckResult.WARN
    assert report.n_observations == 8
    assert report.pbo == 0.0
    assert "other trials are unknown" in report.note


def test_validation_suite_opt_in_uses_configured_family() -> None:
    provider = MemoryBarProvider(n_days=83)
    _, report = run_validation_suite(
        provider.all_bars(),
        provider.get_instruments(),
        config=ValidationConfig(
            lookback=4,
            lookbacks=(3, 4),
            cscv_blocks=4,
            n_boot=10,
            n_perm=10,
        ),
    )
    assert report.overfitting.selection == "cscv_max_mean_return"
    assert report.overfitting.n_trials == 2
    assert report.overfitting.n_blocks == 4
    assert report.overfitting.status in (CheckResult.WARN, CheckResult.NOT_TESTED)
    assert report.deflated_sharpe.status is CheckResult.NOT_TESTED
    assert report.deflated_sharpe.deflated_sharpe is None
