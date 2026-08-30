import pytest

from quantlab.domain.research import CheckResult
from quantlab.research.multiple_testing import (
    CorrectionMethod,
    benjamini_hochberg,
    bonferroni,
    deflated_sharpe,
    evaluate_family,
    holm,
    probability_of_backtest_overfitting,
)
from quantlab.research.statistics import evaluate_returns, moving_block_bootstrap, sign_flip_p_value


def test_block_bootstrap_shape_and_seed() -> None:
    rets = [0.01, -0.02, 0.03, 0.0, -0.01, 0.02, 0.01, -0.01]
    a = moving_block_bootstrap(rets, block_size=3, n_boot=20, seed=1)
    b = moving_block_bootstrap(rets, block_size=3, n_boot=20, seed=1)
    assert a.shape == (20, 8)
    assert a.tolist() == b.tolist()


def test_sign_flip_p_value_in_unit_interval() -> None:
    rets = [0.01] * 10 + [-0.005] * 10
    p_value = sign_flip_p_value(rets, n_perm=50, seed=2)
    assert p_value is not None
    assert 0.0 < p_value <= 1.0


def test_evaluate_returns_small_sample_not_tested() -> None:
    report = evaluate_returns([0.01, -0.01], seed=0)
    assert report.status is CheckResult.NOT_TESTED
    assert report.mean_ci_low is None


def test_evaluate_returns_has_ci() -> None:
    rets = [0.01, -0.005, 0.002, 0.0, 0.003, -0.001, 0.004, 0.001, -0.002]
    report = evaluate_returns(rets, seed=3, n_boot=50, n_perm=50)
    assert report.status is CheckResult.PASS
    assert report.mean_ci_low is not None
    assert report.mean_ci_high is not None
    assert report.mean_ci_low <= report.mean_ci_high


def test_benjamini_hochberg_monotonic_adjusted() -> None:
    p_values = [0.01, 0.04, 0.03, 0.20]
    adj = benjamini_hochberg(p_values)
    assert all(0.0 <= v <= 1.0 for v in adj)
    ranked = sorted(zip(p_values, adj, strict=True), key=lambda x: x[0])
    adjusted = [p[1] for p in ranked]
    assert adjusted == sorted(adjusted)


def test_bonferroni_and_holm() -> None:
    p_values = [0.01, 0.02]
    bon = bonferroni(p_values)
    hol = holm(p_values)
    assert bon[0] == pytest.approx(0.02)
    assert hol[0] <= bon[0]


def test_family_discoveries() -> None:
    report = evaluate_family([0.001, 0.2, 0.3], method=CorrectionMethod.BENJAMINI_HOCHBERG)
    assert report.n_hypotheses == 3
    assert report.discoveries >= 1


def test_deflated_sharpe_underidentified() -> None:
    report = deflated_sharpe(1.0, n_trials=1, n_periods=10)
    assert report.status is CheckResult.NOT_TESTED


def test_deflated_sharpe_defined() -> None:
    report = deflated_sharpe(0.5, n_trials=5, n_periods=40)
    assert report.status is CheckResult.PASS
    assert report.deflated_sharpe is not None


def test_pbo_not_manufactured() -> None:
    report = probability_of_backtest_overfitting([1.0] * 4, [0.1] * 4)
    assert report.status is CheckResult.NOT_TESTED
    assert report.pbo is None
