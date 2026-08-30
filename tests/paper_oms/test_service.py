from __future__ import annotations

import threading

import pytest

from quantlab.core.config import LiveSafetyGates
from quantlab.paper_oms.enums import OrderLifecycleState, ReconciliationStatus
from quantlab.paper_oms.errors import PaperSafetyError
from quantlab.paper_oms.library import (
    seed_account,
    seed_decision,
    seed_request,
    seed_snapshot,
    seed_target,
)
from quantlab.paper_oms.service import run_paper_oms
from quantlab.risk.firewall import RiskFirewall
from quantlab.risk.states import RiskState

pytestmark = pytest.mark.paper_oms


def test_seed_run_fills_and_reconciles() -> None:
    result = run_paper_oms()
    assert LiveSafetyGates().live_trading is False
    assert result.live_trading is False
    assert result.orders
    assert result.fills
    assert result.account.cash < 1_000_000.0
    assert result.account.equity > 0
    assert result.reconciliation.status is ReconciliationStatus.RECONCILED
    filled = [item for item in result.orders if item.state is OrderLifecycleState.RECONCILED]
    assert filled
    for order in result.orders:
        total = (
            order.filled_quantity
            + order.remaining_quantity
            + order.cancelled_quantity
            + order.expired_quantity
        )
        assert abs(total - order.rounded_quantity) < 1e-8
    for fill in result.fills:
        assert "broker" not in fill.note.lower() or "not" in fill.note.lower()
        assert fill.execution_price > 0


def test_partial_fill_keeps_residual() -> None:
    result = run_paper_oms(seed_request(execution_policy_id="partial_fill"))
    partials = [
        item
        for item in result.orders
        if item.state is OrderLifecycleState.PARTIALLY_FILLED or item.remaining_quantity > 0
    ]
    assert partials
    assert any(item.remaining_quantity > 0 for item in result.orders)
    assert result.plan.residuals or any(item.residual_quantity >= 0 for item in result.intents)


def test_unknown_liquidity_does_not_fully_fill() -> None:
    snapshot = seed_snapshot(volumes={"NSE:AAA": None, "NSE:BBB": None, "NSE:CCC": None})
    result = run_paper_oms(snapshot=snapshot)
    assert all(order.filled_quantity == 0 for order in result.orders)
    assert all(order.remaining_quantity == order.rounded_quantity for order in result.orders)


def test_live_trading_rejected() -> None:
    with pytest.raises(PaperSafetyError):
        run_paper_oms(seed_request(live_trading=True))


def test_firewall_halt_rejects_new_exposure() -> None:
    result = run_paper_oms(firewall=RiskFirewall(state=RiskState.HALT))
    assert result.exceptions
    assert all(item.state.value == "rejected" for item in result.orders)


def test_idempotent_resubmit() -> None:
    first = run_paper_oms()
    second = run_paper_oms()
    assert first.run.oms_run_id == second.run.oms_run_id
    assert first.run.run_hash == second.run.run_hash
    assert len(first.orders) == len(second.orders)


def test_concurrent_submit_one_run() -> None:
    from quantlab.paper_oms.state import reset

    reset()
    results: list[str] = []

    def _go() -> None:
        results.append(run_paper_oms().run.oms_run_id)

    threads = [threading.Thread(target=_go) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(set(results)) == 1


def test_determinism() -> None:
    from quantlab.paper_oms.state import reset

    a = run_paper_oms()
    reset()
    b = run_paper_oms()
    assert a.run.run_hash == b.run.run_hash
    assert a.plan.order_plan_hash == b.plan.order_plan_hash
    assert [item.intent_hash for item in a.intents] == [item.intent_hash for item in b.intents]
    assert [item.fill_hash for item in a.fills] == [item.fill_hash for item in b.fills]
    assert a.reconciliation.reconciliation_hash == b.reconciliation.reconciliation_hash


def test_pit_future_payload_ignored() -> None:
    request = seed_request()
    request = request.model_copy(
        update={"future_payload_ignored": {"T+1_price": "999", "T+1_volume": "1e12"}}
    )
    a = run_paper_oms(
        request, decision=seed_decision(), target=seed_target(), account=seed_account()
    )
    from quantlab.paper_oms.state import reset

    reset()
    b = run_paper_oms(
        seed_request(), decision=seed_decision(), target=seed_target(), account=seed_account()
    )
    assert a.run.run_hash == b.run.run_hash
    assert a.fills[0].execution_price == b.fills[0].execution_price
