"""In-process + JSON paper OMS state. Survives restart; reset is explicit."""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock

from quantlab.backtest.spec import config_hash
from quantlab.core.config import get_settings
from quantlab.paper_oms.enums import EventType, OrderLifecycleState
from quantlab.paper_oms.errors import PaperOMSError
from quantlab.paper_oms.events import make_event
from quantlab.paper_oms.models import (
    OMSRun,
    OrderEvent,
    PaperAccount,
    PaperFill,
    PaperOMSResult,
    PaperOrder,
    ReconciliationReport,
    ResetRecord,
)

_LOCK = Lock()
_ACCOUNTS: dict[str, PaperAccount] = {}
_ORDERS: dict[str, PaperOrder] = {}
_FILLS: dict[str, PaperFill] = {}
_EVENTS: list[OrderEvent] = []
_RUNS: dict[str, OMSRun] = {}
_RECONS: dict[str, ReconciliationReport] = {}
_RESULTS: dict[str, PaperOMSResult] = {}
_BY_IDEMPOTENCY: dict[str, str] = {}
_LAST_RUN: str | None = None
_RESETS: list[ResetRecord] = []


def default_path() -> Path:
    return Path(get_settings().experiment_ledger_path).with_name("paper_oms_state.json")


def put_account(account: PaperAccount) -> PaperAccount:
    with _LOCK:
        _ACCOUNTS[account.account_id] = account
        return account


def get_account(account_id: str) -> PaperAccount | None:
    if account_id in _ACCOUNTS:
        return _ACCOUNTS[account_id]
    if account_id in {"", "last"} and _ACCOUNTS:
        return next(reversed(_ACCOUNTS.values()))
    return None


def put_result(result: PaperOMSResult, *, idempotency: str) -> PaperOMSResult:
    global _LAST_RUN
    with _LOCK:
        existing_id = _BY_IDEMPOTENCY.get(idempotency)
        if existing_id is not None and existing_id in _RESULTS:
            return _RESULTS[existing_id]
        run = result.run
        _RUNS[run.oms_run_id] = run
        _RESULTS[run.oms_run_id] = result
        _BY_IDEMPOTENCY[idempotency] = run.oms_run_id
        _LAST_RUN = run.oms_run_id
        _ACCOUNTS[result.account.account_id] = result.account
        for order in result.orders:
            _ORDERS[order.order_id] = order
        for fill in result.fills:
            _FILLS[fill.fill_id] = fill
        _EVENTS.extend(result.events)
        _RECONS[run.oms_run_id] = result.reconciliation
        return result


def get_result(run_id: str) -> PaperOMSResult | None:
    run = get_run(run_id)
    if run is None:
        return None
    return _RESULTS.get(run.oms_run_id)


def last_result() -> PaperOMSResult | None:
    if _LAST_RUN is None:
        return None
    return _RESULTS.get(_LAST_RUN)


def put_run(
    run: OMSRun,
    *,
    orders: list[PaperOrder],
    fills: list[PaperFill],
    events: list[OrderEvent],
    recon: ReconciliationReport | None,
    account: PaperAccount,
    idempotency: str,
) -> OMSRun:
    del orders, fills, events, recon, account, idempotency
    _RUNS[run.oms_run_id] = run
    return run


def get_run(run_id: str) -> OMSRun | None:
    if run_id in _RUNS:
        return _RUNS[run_id]
    if run_id in {"", "last"} and _LAST_RUN:
        return _RUNS.get(_LAST_RUN)
    prefix = [item for item in _RUNS if item.startswith(run_id)]
    if len(prefix) == 1:
        return _RUNS[prefix[0]]
    return None


def lookup_idempotency(key: str) -> OMSRun | None:
    run_id = _BY_IDEMPOTENCY.get(key)
    if run_id is None:
        return None
    return _RUNS.get(run_id)


def list_runs() -> list[OMSRun]:
    return list(_RUNS.values())


def list_orders(run_id: str | None = None) -> list[PaperOrder]:
    run = get_run(run_id or "last")
    if run is None:
        return list(_ORDERS.values())
    return [item for item in _ORDERS.values() if item.plan_hash == run.order_plan_hash]


def list_fills(run_id: str | None = None) -> list[PaperFill]:
    orders = {item.order_id for item in list_orders(run_id)}
    if not orders:
        return list(_FILLS.values())
    return [item for item in _FILLS.values() if item.order_id in orders]


def list_events(order_id: str) -> list[OrderEvent]:
    return [item for item in _EVENTS if item.order_id == order_id]


def get_reconciliation(run_id: str) -> ReconciliationReport | None:
    run = get_run(run_id)
    if run is None:
        return None
    return _RECONS.get(run.oms_run_id)


def replace_order(order: PaperOrder) -> None:
    with _LOCK:
        _ORDERS[order.order_id] = order


def persist(path: Path | None = None) -> None:
    target = path or default_path()
    payload = {
        "last_run": _LAST_RUN,
        "accounts": [item.model_dump(mode="json") for item in _ACCOUNTS.values()],
        "orders": [item.model_dump(mode="json") for item in _ORDERS.values()],
        "fills": [item.model_dump(mode="json") for item in _FILLS.values()],
        "events": [item.model_dump(mode="json") for item in _EVENTS],
        "runs": [item.model_dump(mode="json") for item in _RUNS.values()],
        "reconciliations": [item.model_dump(mode="json") for item in _RECONS.values()],
        "idempotency": dict(_BY_IDEMPOTENCY),
        "resets": [item.model_dump(mode="json") for item in _RESETS],
        "results": [item.model_dump(mode="json") for item in _RESULTS.values()],
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def load(path: Path | None = None) -> None:
    global _LAST_RUN
    target = path or default_path()
    if not target.exists():
        return
    payload = json.loads(target.read_text(encoding="utf-8"))
    with _LOCK:
        _ACCOUNTS.clear()
        for row in payload.get("accounts", []):
            account = PaperAccount.model_validate(row)
            _ACCOUNTS[account.account_id] = account
        _ORDERS.clear()
        for row in payload.get("orders", []):
            order = PaperOrder.model_validate(row)
            _ORDERS[order.order_id] = order
        _FILLS.clear()
        for row in payload.get("fills", []):
            fill = PaperFill.model_validate(row)
            _FILLS[fill.fill_id] = fill
        _EVENTS.clear()
        _EVENTS.extend(OrderEvent.model_validate(row) for row in payload.get("events", []))
        _RUNS.clear()
        for row in payload.get("runs", []):
            run = OMSRun.model_validate(row)
            _RUNS[run.oms_run_id] = run
        _RECONS.clear()
        for row in payload.get("reconciliations", []):
            report = ReconciliationReport.model_validate(row)
            _RECONS[report.report_id] = report
        _BY_IDEMPOTENCY.clear()
        _BY_IDEMPOTENCY.update(payload.get("idempotency", {}))
        _RESETS.clear()
        _RESETS.extend(ResetRecord.model_validate(row) for row in payload.get("resets", []))
        _RESULTS.clear()
        for row in payload.get("results", []):
            stored = PaperOMSResult.model_validate(row)
            _RESULTS[stored.run.oms_run_id] = stored
        _LAST_RUN = payload.get("last_run")


def state_hash() -> str:
    return config_hash(
        {
            "accounts": sorted(_ACCOUNTS),
            "orders": sorted(_ORDERS),
            "fills": sorted(_FILLS),
            "runs": sorted(_RUNS),
        }
    )


def reset_state(*, reason: str, timestamp: object) -> ResetRecord:
    from datetime import UTC, datetime

    from quantlab.domain.models import Side
    from quantlab.paper_oms.enums import OrderAction, PaperOrderType, TimeInForce

    global _LAST_RUN
    if not reason.strip():
        raise PaperOMSError("paper account reset requires an explicit reason")
    when = timestamp if isinstance(timestamp, datetime) else datetime(2024, 1, 15, tzinfo=UTC)
    previous = state_hash()
    with _LOCK:
        _ACCOUNTS.clear()
        _ORDERS.clear()
        _FILLS.clear()
        _EVENTS.clear()
        _RUNS.clear()
        _RECONS.clear()
        _RESULTS.clear()
        _BY_IDEMPOTENCY.clear()
        _LAST_RUN = None
        new_hash = state_hash()
        record = ResetRecord(
            reset_id=f"RST-{previous[:8]}",
            previous_state_hash=previous,
            new_state_hash=new_hash,
            reason=reason,
            timestamp=when,
        )
        _RESETS.append(record)
        dummy = PaperOrder(
            order_id="ACCT-RESET",
            idempotency_key="reset",
            plan_id="",
            plan_hash="",
            intent_id="",
            intent_hash="",
            decision_hash="",
            account_id="",
            security_id="CASH",
            side=Side.BUY,
            action=OrderAction.NO_ACTION,
            order_type=PaperOrderType.MARKET,
            time_in_force=TimeInForce.DAY,
            requested_quantity=0.0,
            rounded_quantity=0.0,
            residual_quantity=0.0,
            remaining_quantity=0.0,
            reference_price=0.0,
            created_at=when,
            arrival_time=when,
        )
        _EVENTS.append(
            make_event(
                dummy,
                EventType.ACCOUNT_RESET,
                previous=OrderLifecycleState.CREATED,
                new_state=OrderLifecycleState.CANCELLED,
                sequence=len(_EVENTS) + 1,
                event_time=when,
                note=reason,
            )
        )
        return record


def reset() -> None:
    """Test helper. Production reset must call reset_state with a reason."""
    global _LAST_RUN
    with _LOCK:
        _ACCOUNTS.clear()
        _ORDERS.clear()
        _FILLS.clear()
        _EVENTS.clear()
        _RUNS.clear()
        _RECONS.clear()
        _RESULTS.clear()
        _BY_IDEMPOTENCY.clear()
        _RESETS.clear()
        _LAST_RUN = None
