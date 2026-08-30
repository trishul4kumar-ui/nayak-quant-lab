from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.domain.research import CheckResult
from quantlab.paper_oms.errors import InsufficientCashError
from quantlab.paper_oms.library import seed_account, seed_decision, seed_snapshot, seed_target
from quantlab.paper_oms.service import run_paper_oms
from quantlab.research.integrity import evaluate_integrity

pytestmark = pytest.mark.paper_oms


def test_cash_and_equity_identity() -> None:
    result = run_paper_oms()
    ledger = result.account.ledger
    assert ledger is not None
    expected = ledger.opening_cash + ledger.deposits - ledger.purchases + ledger.sales
    assert abs(expected - ledger.closing_cash) < 1e-6
    assert abs(result.account.cash + result.account.market_value - result.account.equity) < 1e-6


def test_insufficient_cash_rejects() -> None:
    result = run_paper_oms(account=seed_account(cash=1.0))
    assert result.exceptions
    assert any("cash" in item.lower() for item in result.exceptions)
    assert all(item.filled_quantity == 0 for item in result.orders)


def test_integrity_flags_default_not_tested() -> None:
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
        duplicate_order=True,
    )
    assert report.checks["duplicate_order"] is CheckResult.FAIL
    assert report.checks["orphan_fill"] is CheckResult.NOT_TESTED


def test_end_to_end_ledger_and_knowledge(tmp_path: Path) -> None:
    from quantlab import __version__
    from quantlab.knowledge.entities import NodeType
    from quantlab.knowledge.ingest import persist_paper_oms
    from quantlab.knowledge.serialization import load_graph
    from quantlab.paper_oms.experiment import run_paper_experiment

    result, run = run_paper_experiment(ledger_path=tmp_path / "ledger.jsonl")
    assert __version__ == "3.1.0"
    assert run.selection_stage == "paper_oms"
    assert run.oms_run_id == result.run.oms_run_id
    persist_paper_oms(result, seed_decision(), tmp_path / "ledger.jsonl")
    graph = load_graph(tmp_path / "knowledge.json")
    types = {item.node_type for item in graph.nodes}
    assert NodeType.PAPER_ORDER in types
    assert NodeType.PAPER_FILL in types
    assert NodeType.RECONCILIATION in types
    assert NodeType.ORDER_PLAN in types


def test_insufficient_cash_error_type() -> None:
    with pytest.raises(InsufficientCashError):
        from quantlab.paper_oms.intent import intents_from_target
        from quantlab.paper_oms.orders import order_from_instruction
        from quantlab.paper_oms.planner import plan_orders
        from quantlab.paper_oms.policy import resolve_policy
        from quantlab.paper_oms.validation import validate_order

        plan = plan_orders(
            intents_from_target(seed_decision(), seed_target(), seed_account(), seed_snapshot()),
            seed_account(),
            seed_snapshot(),
            resolve_policy("base"),
        )
        order = order_from_instruction(
            plan.instructions[0], plan, account_id="x", decision_hash="h"
        )
        validate_order(order, seed_account(cash=1.0), seed_snapshot())
