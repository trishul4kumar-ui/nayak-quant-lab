from __future__ import annotations

import math

import pytest

from quantlab import __version__
from quantlab.core.errors import SafetyError
from quantlab.domain.research import CheckResult
from quantlab.monitoring.benchmark import nifty_placeholder
from quantlab.monitoring.concentration import herfindahl
from quantlab.monitoring.enums import AttributionMethod, BenchmarkKind, ReturnKind
from quantlab.monitoring.library import seed_paper_result
from quantlab.monitoring.models import MonitoringRequest
from quantlab.monitoring.pnl import equity_identity, pnl_from_account
from quantlab.monitoring.returns import log_return, report_returns, simple_return
from quantlab.monitoring.service import run_monitoring
from quantlab.monitoring.state import reset as reset_monitoring


def _run():
    paper, decision, target = seed_paper_result()
    return run_monitoring(paper=paper, decision=decision, target=target), paper, decision, target


def test_version() -> None:
    assert __version__ == "3.1.0"


def test_equity_identity() -> None:
    paper, _, _ = seed_paper_result()
    equity_identity(paper.account)
    expected = paper.account.cash + paper.account.market_value
    assert abs(expected - paper.account.equity) < 1e-6


def test_pnl_realized_unrealized_plus_residual() -> None:
    paper, _, _ = seed_paper_result()
    ledger = paper.account.ledger
    start = ledger.opening_cash if ledger is not None else paper.account.equity
    pnl = pnl_from_account(paper.account, beginning_equity=start, fills=paper.fills)
    explained = pnl.realized_pnl + pnl.unrealized_pnl
    assert abs(pnl.pnl_total - explained - pnl.residual_pnl) < 1e-6
    assert pnl.income is None
    assert pnl.financing is None
    assert pnl.adjustments is None


def test_unknown_legs_are_none() -> None:
    paper, _, _ = seed_paper_result()
    pnl = pnl_from_account(paper.account, beginning_equity=1_000_000.0, fills=paper.fills)
    assert pnl.income is None
    assert pnl.financing is None


@pytest.mark.parametrize("kind", list(ReturnKind))
def test_return_kinds_exist(kind: ReturnKind) -> None:
    rows = report_returns(
        beginning=1_000_000.0,
        ending=1_010_000.0,
        period_returns=[0.01],
        risk_free=0.0,
    )
    assert any(row.kind is kind for row in rows)


def test_simple_and_log_return() -> None:
    assert simple_return(100.0, 110.0) == pytest.approx(0.1)
    assert log_return(100.0, 110.0) == pytest.approx(math.log(1.1))
    assert simple_return(0.0, 1.0) is None


def test_no_annualize_with_few_obs() -> None:
    rows = report_returns(beginning=100.0, ending=110.0, period_returns=[0.1], risk_free=0.0)
    simple = next(row for row in rows if row.kind is ReturnKind.SIMPLE)
    assert simple.annualized is None


def test_security_attribution_reconciles() -> None:
    result, paper, _, _ = _run()
    attr = result.attribution
    explained = sum(row.pnl for row in attr.contributions)
    assert abs(explained + attr.residual - attr.total) < 1e-6
    assert attr.method is AttributionMethod.EXACT_ACCOUNTING


def test_factor_attribution_not_tested_without_inputs() -> None:
    result, _, _, _ = _run()
    assert result.factor_attribution.status is CheckResult.NOT_TESTED
    assert result.factor_attribution.method is AttributionMethod.UNAVAILABLE


def test_factor_attribution_when_supplied() -> None:
    paper, decision, target = seed_paper_result()
    result = run_monitoring(
        MonitoringRequest(
            factor_returns={"mkt": 0.01},
            factor_exposures={"mkt": 0.5},
        ),
        paper=paper,
        decision=decision,
        target=target,
    )
    assert result.factor_attribution.method is AttributionMethod.MODEL_BASED
    assert result.factor_attribution.factor_contributions is not None


def test_alpha_lineage_unavailable() -> None:
    result, _, _, _ = _run()
    assert result.alpha_attribution.method is AttributionMethod.UNAVAILABLE


def test_alpha_lineage_estimated() -> None:
    paper, decision, target = seed_paper_result()
    result = run_monitoring(
        MonitoringRequest(alpha_lineage={"alpha": 0.6, "execution": 0.4}),
        paper=paper,
        decision=decision,
        target=target,
    )
    assert result.alpha_attribution.method is AttributionMethod.ESTIMATED
    pieces = sum(result.alpha_attribution.alpha_contributions.values())  # type: ignore[union-attr]
    assert abs(pieces + result.alpha_attribution.residual - result.pnl.pnl_total) < 1e-6


def test_nifty_not_tested() -> None:
    bench = nifty_placeholder()
    assert bench.kind is BenchmarkKind.INDEX
    assert bench.status is CheckResult.NOT_TESTED


def test_drift_does_not_rebalance() -> None:
    result, paper, _, target = _run()
    assert result.drift.note.startswith("Observed")
    assert paper.account.equity == result.pnl.ending_equity
    assert target.portfolio_id == "TP-PAPER-SEED"


def test_drawdown_and_concentration() -> None:
    result, paper, _, _ = _run()
    assert result.drawdown.max_drawdown <= 0.0
    assert herfindahl(paper.account) == pytest.approx(result.concentration)


def test_feedback_is_not_hypothesis() -> None:
    result, _, _, _ = _run()
    assert result.feedback
    assert all(not item.is_hypothesis for item in result.feedback)


def test_live_trading_rejected() -> None:
    paper, decision, target = seed_paper_result()
    with pytest.raises(SafetyError):
        run_monitoring(
            MonitoringRequest(live_trading=True),
            paper=paper,
            decision=decision,
            target=target,
        )


def test_future_payload_ignored() -> None:
    paper, decision, target = seed_paper_result()
    a = run_monitoring(
        MonitoringRequest(future_payload_ignored={"close": "999"}),
        paper=paper,
        decision=decision,
        target=target,
    )
    reset_monitoring()
    b = run_monitoring(paper=paper, decision=decision, target=target)
    assert a.run.run_hash == b.run.run_hash


def test_determinism() -> None:
    paper, decision, target = seed_paper_result()
    a = run_monitoring(paper=paper, decision=decision, target=target)
    reset_monitoring()
    b = run_monitoring(paper=paper, decision=decision, target=target)
    assert a.run.run_hash == b.run.run_hash
    assert a.run.performance_hash == b.run.performance_hash
    assert a.run.attribution_hash == b.run.attribution_hash


def test_idempotent_resubmit() -> None:
    paper, decision, target = seed_paper_result()
    a = run_monitoring(paper=paper, decision=decision, target=target)
    b = run_monitoring(paper=paper, decision=decision, target=target)
    assert a.run.monitoring_run_id == b.run.monitoring_run_id


def test_knowledge_and_ledger(tmp_path) -> None:
    from quantlab.domain.models import ExperimentRun
    from quantlab.knowledge.ingest import persist_monitoring
    from quantlab.knowledge.serialization import load_graph
    from quantlab.monitoring.experiment import run_monitoring_experiment

    paper, decision, target = seed_paper_result()
    ledger = tmp_path / "ledger.jsonl"
    result, row = run_monitoring_experiment(
        ledger_path=ledger, paper=paper, decision=decision, target=target
    )
    persist_monitoring(result, decision, ledger)
    graph = load_graph(ledger.with_name("knowledge.json"))
    types = {node.node_type.value for node in graph.nodes}
    assert "performance_run" in types
    assert "research_feedback" in types
    assert row.monitoring_run_id == result.run.monitoring_run_id
    assert ExperimentRun.model_fields["residual_pnl"]


@pytest.mark.parametrize(
    "flag",
    [
        "future_performance_mark",
        "hidden_residual",
        "pnl_reconciliation_break",
        "attribution_reconciliation_break",
        "performance_claim_overstatement",
    ],
)
def test_integrity_flags_fail_when_set(flag: str) -> None:
    from quantlab.research.integrity import evaluate_integrity

    report = evaluate_integrity(
        bars=[],
        states=[],
        as_of_times=[],
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="configured",
        live_trading=False,
        n_experiments_in_family=1,
        used_ml=False,
        **{flag: True},
    )
    assert report.checks[flag] is CheckResult.FAIL


def test_broker_import_absent() -> None:
    from pathlib import Path

    root = Path("src/quantlab/monitoring")
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "kiteconnect" not in text
        assert "zerodha" not in text
        assert "openalgo" not in text
        assert "quantlab.brokers" not in text


def test_old_ledger_row_loads() -> None:
    from quantlab.domain.models import ExperimentRun

    row = ExperimentRun(
        id="old",
        name="legacy",
        hypothesis="h",
        dataset_version="v",
        universe=[],
    )
    assert row.monitoring_run_id == ""
    assert row.tca_run_id == ""
