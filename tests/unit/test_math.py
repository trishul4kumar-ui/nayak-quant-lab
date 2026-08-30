import pytest

from quantlab.math.metrics import (
    cagr,
    max_drawdown,
    sharpe,
    simple_returns,
    summarize_equity,
    zscore,
)


def test_simple_returns() -> None:
    got = simple_returns([100.0, 110.0, 121.0])
    assert got[0] == pytest.approx(0.1)
    assert got[1] == pytest.approx(0.1)


def test_zscore_zero_variance() -> None:
    assert zscore([2.0, 2.0, 2.0]) == [0.0, 0.0, 0.0]


def test_max_drawdown() -> None:
    assert max_drawdown([100.0, 120.0, 90.0, 95.0]) == pytest.approx(-0.25)


def test_summarize_has_required_keys() -> None:
    metrics = summarize_equity([1_000_000.0, 1_010_000.0, 1_020_000.0], [0.1, 0.1], 0.001)
    for key in ("total_return", "cagr", "sharpe", "sortino", "max_drawdown", "win_rate"):
        assert key in metrics


def test_sharpe_flat() -> None:
    assert sharpe([0.0, 0.0, 0.0]) == 0.0


def test_cagr_identity() -> None:
    assert cagr([100.0, 100.0]) == 0.0
