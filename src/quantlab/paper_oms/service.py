"""Paper OMS service. Target → intent → plan → paper order → fill → position → recon."""

from __future__ import annotations

from datetime import datetime

from quantlab.capital.definitions import InvestmentDecision, TargetPortfolio
from quantlab.domain.models import Side
from quantlab.domain.research import IntegrityReport
from quantlab.execution_research.definition import ExecutionLeakFlags
from quantlab.paper_oms.accounting import apply_fill, assert_cash_identity, reserve_buy
from quantlab.paper_oms.enums import (
    EventType,
    OMSRunStatus,
    OrderLifecycleState,
    ReconciliationStatus,
    RemainderFate,
)
from quantlab.paper_oms.errors import (
    InsufficientCashError,
    InsufficientPositionError,
    InvalidOrderTransition,
    OMSValidationError,
    PaperOMSError,
    UnsupportedOrderTypeError,
)
from quantlab.paper_oms.events import make_event
from quantlab.paper_oms.execution import PaperExecutionAdapter
from quantlab.paper_oms.fills import apply_fill_to_order, quantity_identity
from quantlab.paper_oms.identity import hash_run, idempotency_key
from quantlab.paper_oms.integrity import PaperOMSLeakFlags
from quantlab.paper_oms.intent import intents_from_target
from quantlab.paper_oms.library import seed_account, seed_decision, seed_snapshot, seed_target
from quantlab.paper_oms.models import (
    OMSRun,
    OrderEvent,
    PaperAccount,
    PaperFill,
    PaperMarketSnapshot,
    PaperOMSRequest,
    PaperOMSResult,
    PaperOrder,
)
from quantlab.paper_oms.orders import advance, order_from_instruction
from quantlab.paper_oms.planner import plan_orders
from quantlab.paper_oms.policy import resolve_policy
from quantlab.paper_oms.reconciliation import reconcile
from quantlab.paper_oms.reporting import tca_report
from quantlab.paper_oms.safety import assert_paper_only
from quantlab.paper_oms.state import get_result, lookup_idempotency, put_account, put_result
from quantlab.paper_oms.validation import validate_order
from quantlab.research.integrity import evaluate_integrity
from quantlab.risk.firewall import RiskFirewall


def _integrity(flags: PaperOMSLeakFlags, *, live_trading: bool, data_kind: str) -> IntegrityReport:
    return evaluate_integrity(
        bars=[],
        states=[],
        as_of_times=[],
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="configured",
        live_trading=live_trading,
        n_experiments_in_family=1,
        used_ml=False,
        data_kind=data_kind,
        target_mutation=flags.target_mutation,
        decision_hash_mismatch=flags.decision_hash_mismatch,
        order_intent_mutation=flags.order_intent_mutation,
        order_plan_mutation=flags.order_plan_mutation,
        duplicate_order=flags.duplicate_order,
        duplicate_fill=flags.duplicate_fill,
        invalid_order_transition=flags.invalid_order_transition,
        pre_arrival_fill=flags.pre_arrival_fill,
        future_execution_price=flags.future_execution_price,
        future_fill_information=flags.future_fill_information,
        future_liquidity_leak=flags.future_liquidity_leak,
        full_fill_assumption=flags.full_fill_assumption,
        hidden_partial_fill=flags.hidden_partial_fill,
        cash_accounting_break=flags.cash_accounting_break,
        position_accounting_break=flags.position_accounting_break,
        target_position_mismatch=flags.target_position_mismatch,
        order_fill_mismatch=flags.order_fill_mismatch,
        orphan_fill=flags.orphan_fill,
        orphan_event=flags.orphan_event,
        reconciliation_break=flags.reconciliation_break,
        execution_policy_mutation=flags.execution_policy_mutation,
        paper_live_mode_confusion=flags.paper_live_mode_confusion,
        broker_import_violation=flags.broker_import_violation,
    )


def run_paper_oms(
    request: PaperOMSRequest | None = None,
    *,
    decision: InvestmentDecision | None = None,
    target: TargetPortfolio | None = None,
    account: PaperAccount | None = None,
    snapshot: PaperMarketSnapshot | None = None,
    firewall: RiskFirewall | None = None,
    leaks: PaperOMSLeakFlags | None = None,
    execution_leaks: ExecutionLeakFlags | None = None,
) -> PaperOMSResult:
    used = request or PaperOMSRequest()
    assert_paper_only(live_trading=used.live_trading)
    _ignored = used.future_payload_ignored
    del _ignored
    flags = leaks or PaperOMSLeakFlags()
    used_decision = decision or seed_decision()
    used_target = target or seed_target()
    used_account = account or seed_account(allow_short=used.allow_short)
    used_snapshot = snapshot or seed_snapshot()
    put_account(used_account)
    if used_target.decision_id != used_decision.decision_id:
        flags = flags.model_copy(update={"target_mutation": True})
        raise PaperOMSError("target_mutation: target does not belong to this decision")
    policy = resolve_policy(used.execution_policy_id)
    intents = intents_from_target(
        used_decision,
        used_target,
        used_account,
        used_snapshot,
        lot_size=used.lot_size,
        min_trade_quantity=used.min_trade_quantity,
    )
    plan = plan_orders(intents, used_account, used_snapshot, policy)
    key = idempotency_key(
        decision_hash=used_decision.decision_hash,
        account_id=used_account.account_id,
        snapshot_id=used_snapshot.snapshot_id,
        execution_policy_id=policy.policy_id,
        plan_hash=plan.order_plan_hash,
    )
    existing = lookup_idempotency(key)
    if existing is not None:
        cached = get_result(existing.oms_run_id)
        if cached is not None:
            flags = flags.model_copy(update={"duplicate_order": False})
            return cached

    events: list[OrderEvent] = []
    orders: list[PaperOrder] = []
    fills: list[PaperFill] = []
    exceptions: list[str] = []
    seen_fills: set[str] = set()
    adapter = PaperExecutionAdapter(policy)
    books = used_account

    if not intents:
        status = OMSRunStatus.ABSTAINED
        recon = reconcile(
            target=used_target,
            account=books,
            orders=[],
            fills=[],
            events=[],
            snapshot_prices=used_snapshot.prices,
            equity=books.equity,
        )
        run = _freeze_run(
            used_decision,
            used_snapshot,
            books,
            policy.policy_id,
            plan.order_plan_hash,
            plan.intent_hash,
            status,
            recon.status,
            0,
            0,
            used_snapshot.as_of,
            policy.random_seed,
        )
        tca = tca_report(target_notional=0.0, fills=[], residual_notional=0.0)
        integrity = _integrity(flags, live_trading=False, data_kind=used.data_kind)
        result = PaperOMSResult(
            run=run,
            decision_id=used_decision.decision_id,
            intents=[],
            plan=plan,
            account=books,
            reconciliation=recon,
            tca=tca,
            live_trading=False,
            note="No paper orders: abstain/reject/no-action.",
        )
        del integrity
        return put_result(result, idempotency=key)

    for instruction in plan.instructions:
        order = order_from_instruction(
            instruction,
            plan,
            account_id=books.account_id,
            decision_hash=used_decision.decision_hash,
        )
        events.append(
            make_event(
                order,
                EventType.ORDER_CREATED,
                previous=None,
                new_state=OrderLifecycleState.CREATED,
                sequence=len(events) + 1,
                event_time=order.created_at,
            )
        )
        try:
            order = advance(order, OrderLifecycleState.VALIDATED, events, EventType.ORDER_VALIDATED)
            validate_order(order, books, used_snapshot, firewall=firewall)
            order = advance(order, OrderLifecycleState.PLANNED, events, EventType.ORDER_PLANNED)
            if instruction.side is Side.BUY:
                books = reserve_buy(
                    books, instruction.rounded_quantity * instruction.reference_price
                )
            order = advance(
                order,
                OrderLifecycleState.SUBMITTED_PAPER,
                events,
                EventType.ORDER_SUBMITTED_PAPER,
            )
            order = advance(
                order, OrderLifecycleState.ACKNOWLEDGED, events, EventType.ORDER_SUBMITTED_PAPER
            )
            fill = adapter.simulate(order, used_snapshot, leaks=execution_leaks)
            if fill.fill_time < fill.arrival_time:
                flags = flags.model_copy(update={"pre_arrival_fill": True})
                raise PaperOMSError("pre_arrival_fill")
            events.append(
                make_event(
                    order,
                    EventType.PAPER_FILL_RECEIVED,
                    previous=order.state,
                    new_state=order.state,
                    sequence=len(events) + 1,
                    event_time=fill.fill_time,
                    note="simulated paper fill; not broker-confirmed",
                )
            )
            remainder = used.remainder_fate
            if used.cancel_unfilled and fill.remaining_quantity > 0:
                remainder = RemainderFate.CANCELLED_REMAINDER
            try:
                order = apply_fill_to_order(
                    order, fill, seen_fill_ids=seen_fills, remainder=remainder
                )
            except PaperOMSError:
                flags = flags.model_copy(update={"duplicate_fill": True})
                raise
            seen_fills.add(fill.fill_id)
            if not quantity_identity(order):
                flags = flags.model_copy(update={"order_fill_mismatch": True})
            books = apply_fill(books, fill, used_snapshot)
            fills.append(fill)
            if order.remaining_quantity > 1e-12:
                order = advance(
                    order,
                    OrderLifecycleState.PARTIALLY_FILLED,
                    events,
                    EventType.ORDER_PARTIALLY_FILLED,
                )
                if remainder is RemainderFate.CANCELLED_REMAINDER:
                    order = advance(
                        order, OrderLifecycleState.CANCELLED, events, EventType.ORDER_CANCELLED
                    )
                elif remainder is RemainderFate.EXPIRED_REMAINDER:
                    order = advance(
                        order, OrderLifecycleState.EXPIRED, events, EventType.ORDER_EXPIRED
                    )
            else:
                order = advance(order, OrderLifecycleState.FILLED, events, EventType.ORDER_FILLED)
                order = advance(
                    order, OrderLifecycleState.RECONCILED, events, EventType.ORDER_RECONCILED
                )
        except (
            OMSValidationError,
            InsufficientCashError,
            InsufficientPositionError,
            UnsupportedOrderTypeError,
        ) as exc:
            if order.state not in {
                OrderLifecycleState.REJECTED,
                OrderLifecycleState.FAILED,
            }:
                try:
                    order = advance(
                        order,
                        OrderLifecycleState.REJECTED,
                        events,
                        EventType.ORDER_REJECTED,
                        reason=str(exc),
                    )
                except InvalidOrderTransition:
                    order = order.model_copy(
                        update={"state": OrderLifecycleState.REJECTED, "rejection_reason": str(exc)}
                    )
            exceptions.append(str(exc))
        orders.append(order)

    try:
        assert_cash_identity(books)
    except PaperOMSError:
        flags = flags.model_copy(update={"cash_accounting_break": True})
        raise
    recon = reconcile(
        target=used_target,
        account=books,
        orders=orders,
        fills=fills,
        events=events,
        snapshot_prices=used_snapshot.prices,
        equity=books.equity,
    )
    if recon.status is ReconciliationStatus.RECONCILIATION_BREAK:
        flags = flags.model_copy(update={"reconciliation_break": True})
        if "orphan_fill" in recon.breaks:
            flags = flags.model_copy(update={"orphan_fill": True})
        if "orphan_event" in recon.breaks:
            flags = flags.model_copy(update={"orphan_event": True})
        if "order_fill_mismatch" in recon.breaks:
            flags = flags.model_copy(update={"order_fill_mismatch": True})
        if "cash_mismatch" in recon.breaks:
            flags = flags.model_copy(update={"cash_accounting_break": True})
        if "target_position_mismatch" in recon.breaks:
            flags = flags.model_copy(update={"target_position_mismatch": True})
    else:
        flags = flags.model_copy(
            update={
                "reconciliation_break": False,
                "orphan_fill": False,
                "orphan_event": False,
                "cash_accounting_break": False,
            }
        )
    flags = flags.model_copy(
        update={
            "duplicate_order": False,
            "paper_live_mode_confusion": False,
            "broker_import_violation": False,
            "pre_arrival_fill": False if flags.pre_arrival_fill is None else flags.pre_arrival_fill,
        }
    )
    integrity = _integrity(flags, live_trading=False, data_kind=used.data_kind)
    target_notional = sum(abs(v) for v in used_target.notional_targets.values())
    residual_notional = sum(item.residual_notional for item in intents) + sum(
        item.remaining_quantity * item.reference_price for item in orders
    )
    tca = tca_report(
        target_notional=target_notional, fills=fills, residual_notional=residual_notional
    )
    run_status = OMSRunStatus.COMPLETED
    if exceptions and not fills:
        run_status = OMSRunStatus.REJECTED
    elif exceptions:
        run_status = OMSRunStatus.COMPLETED
    run = _freeze_run(
        used_decision,
        used_snapshot,
        books,
        policy.policy_id,
        plan.order_plan_hash,
        plan.intent_hash,
        run_status,
        recon.status,
        len(orders),
        len(fills),
        used_snapshot.as_of,
        policy.random_seed,
    )
    result = PaperOMSResult(
        run=run,
        decision_id=used_decision.decision_id,
        intents=intents,
        plan=plan,
        orders=orders,
        fills=fills,
        events=events,
        account=books,
        reconciliation=recon,
        tca=tca,
        exceptions=exceptions,
        live_trading=False,
    )
    del integrity
    return put_result(result, idempotency=key)


def _freeze_run(
    decision: InvestmentDecision,
    snapshot: PaperMarketSnapshot,
    account: PaperAccount,
    policy_id: str,
    plan_hash: str,
    intent_hash: str,
    status: OMSRunStatus,
    recon: ReconciliationStatus,
    order_count: int,
    fill_count: int,
    as_of: datetime,
    seed: int,
) -> OMSRun:
    run = OMSRun(
        oms_run_id="",
        decision_hash=decision.decision_hash,
        snapshot_id=snapshot.snapshot_id,
        account_id=account.account_id,
        execution_policy_id=policy_id,
        started_at=as_of,
        completed_at=as_of,
        status=status,
        order_count=order_count,
        fill_count=fill_count,
        reconciliation_status=recon,
        order_plan_hash=plan_hash,
        intent_hash=intent_hash,
        random_seed=seed,
        live_trading=False,
    )
    hashed = hash_run(run)
    return run.model_copy(update={"run_hash": hashed, "oms_run_id": f"OMS-{hashed[:12]}"})
