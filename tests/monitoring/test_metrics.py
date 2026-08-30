from __future__ import annotations

import pytest

from quantlab.app.monitoring import list_payload, run_payload
from quantlab.monitoring.concentration import herfindahl
from quantlab.monitoring.drawdown import drawdown_from_path
from quantlab.monitoring.exposure import exposure_map
from quantlab.monitoring.library import seed_paper_result
from quantlab.monitoring.models import EquityPoint
from quantlab.monitoring.reconciliation import reconcile_attribution, reconcile_pnl
from quantlab.monitoring.returns import cumulative_from_simple, downside_deviation, rolling_sharpe
from quantlab.monitoring.service import run_monitoring
from quantlab.monitoring.turnover import fill_turnover
from quantlab.paper_oms.library import SEED_NAMES


@pytest.mark.parametrize("name", list(SEED_NAMES))
def test_each_seed_name_can_contribute(name: str) -> None:
    result, paper, _, _ = _bundle()
    ids = {row.security_id for row in result.attribution.contributions}
    in_book = name in paper.account.positions
    assert name in ids or in_book or result.attribution.residual is not None


def _bundle():
    paper, decision, target = seed_paper_result()
    result = run_monitoring(paper=paper, decision=decision, target=target)
    return result, paper, decision, target


@pytest.mark.parametrize("mult", [0.5, 1.0, 1.5, 2.0])
def test_cumulative_return(mult: float) -> None:
    assert cumulative_from_simple([mult - 1.0]) == pytest.approx(mult - 1.0)


@pytest.mark.parametrize("n", [1, 2, 5, 10])
def test_sharpe_insufficient_or_defined(n: int) -> None:
    returns = [0.01 * ((-1) ** i) for i in range(n)]
    if n < 2:
        assert rolling_sharpe(returns, risk_free=0.0) is None
    else:
        val = rolling_sharpe(returns, risk_free=0.0)
        assert val is None or isinstance(val, float)


@pytest.mark.parametrize("mar", [0.0, -0.01, 0.01])
def test_downside_deviation(mar: float) -> None:
    out = downside_deviation([0.02, -0.03, -0.01, 0.04], mar=mar)
    assert out is None or out >= 0.0


def test_exposure_map_keys() -> None:
    paper, _, _ = seed_paper_result()
    exp = exposure_map(paper.account)
    for key in ("gross", "net", "long", "short", "cash", "equity"):
        assert key in exp


def test_turnover_non_negative() -> None:
    paper, _, _ = seed_paper_result()
    assert fill_turnover(paper.fills, equity=paper.account.equity) >= 0.0


def test_drawdown_single_point() -> None:
    from datetime import UTC, datetime

    path = [
        EquityPoint(
            as_of=datetime(2024, 1, 15, tzinfo=UTC),
            cash=1.0,
            market_value=0.0,
            equity=1.0,
        )
    ]
    obs = drawdown_from_path(path)
    assert obs.current_drawdown == 0.0


def test_reconcile_helpers() -> None:
    result, _, _, _ = _bundle()
    assert reconcile_pnl(result.pnl) == []
    assert reconcile_attribution(result.pnl, result.attribution) == []


def test_equal_weight_benchmark_labelled() -> None:
    result, _, _, _ = _bundle()
    assert "synthetic" in result.benchmark.benchmark_id
    assert "nifty" not in result.benchmark.benchmark_id


def test_cli_run_and_list(tmp_path) -> None:
    payload = run_payload(ledger=str(tmp_path / "ledger.jsonl"))
    assert payload["live_trading"] is False
    rows = list_payload()
    assert rows
    assert rows[0].get("live_trading") is False


@pytest.mark.parametrize("cmd", ["performance", "pnl", "drift", "feedback", "report"])
def test_app_payloads(cmd: str) -> None:
    from quantlab.app import monitoring as app

    run_payload()
    fn = {
        "performance": app.performance_payload,
        "pnl": app.pnl_payload,
        "drift": app.drift_payload,
        "feedback": app.feedback_payload,
        "report": app.report_payload,
    }[cmd]
    out = fn()
    assert out is not None


@pytest.mark.parametrize(
    "field",
    [
        "beginning_equity",
        "ending_equity",
        "cash",
        "realized_pnl",
        "unrealized_pnl",
        "residual_pnl",
        "pnl_total",
    ],
)
def test_pnl_fields_present(field: str) -> None:
    result, _, _, _ = _bundle()
    assert hasattr(result.pnl, field)


def test_herfindahl_bounds() -> None:
    paper, _, _ = seed_paper_result()
    h = herfindahl(paper.account)
    assert 0.0 <= h <= 1.0 + 1e-9


def test_seed_account_empty_hhi() -> None:
    from quantlab.paper_oms.library import seed_account

    assert herfindahl(seed_account()) == 0.0
