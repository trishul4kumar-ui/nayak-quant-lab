from quantlab.math.annualization import DEFAULT_ANNUALIZATION
from quantlab.math.drawdown import average_drawdown, top_drawdowns
from quantlab.math.metrics import max_drawdown, summarize_equity


def test_max_drawdown_non_positive() -> None:
    equity = [100.0, 120.0, 90.0, 95.0, 130.0]
    assert max_drawdown(equity) <= 0
    assert average_drawdown(equity) <= 0


def test_top_drawdowns_include_recovery() -> None:
    equity = [100.0, 110.0, 80.0, 90.0, 120.0]
    found = top_drawdowns(equity, n=3)
    assert found
    assert found[0].drawdown <= 0
    assert found[0].recovery_index is not None


def test_summarize_has_distribution_keys() -> None:
    metrics = summarize_equity(
        [1_000_000.0, 1_010_000.0, 990_000.0, 1_020_000.0], [0.1, 0.2, 0.1], 0.001
    )
    for key in (
        "skewness",
        "excess_kurtosis",
        "tail_loss_5pct",
        "annual_turnover",
        "average_drawdown",
    ):
        assert key in metrics


def test_annualization_is_explicit() -> None:
    assert DEFAULT_ANNUALIZATION.sessions_per_year == 252
    assert DEFAULT_ANNUALIZATION.risk_free_rate == 0.0
    assert "not_indian_t_bill" in DEFAULT_ANNUALIZATION.risk_free_convention
