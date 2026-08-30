"""quantlab paper commands. Paper OMS only. No broker routing."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from quantlab.app.paper_oms import (
    audit_payload,
    cancel_payload,
    cash_payload,
    create_payload,
    events_payload,
    exceptions_payload,
    fills_payload,
    inspect_payload,
    list_payload,
    orders_payload,
    plan_payload,
    positions_payload,
    reconcile_payload,
    report_payload,
    residuals_payload,
    submit_payload,
    tca_payload,
    validate_payload,
)


def add_paper_parser(sub: Any) -> None:
    parser = sub.add_parser("paper", help="paper OMS / order lifecycle (not live)")
    cmd = parser.add_subparsers(dest="paper_cmd", required=True)
    cmd.add_parser("list", help="list paper OMS runs")
    inspect_p = cmd.add_parser("inspect", help="inspect a paper OMS run")
    inspect_p.add_argument("item_id", nargs="?", default="last")
    cmd.add_parser("create", help="create the seed paper account")
    plan_p = cmd.add_parser("plan", help="plan paper orders from a decision")
    plan_p.add_argument("item_id", nargs="?", default="last")
    plan_p.add_argument("--policy", default="base")
    val = cmd.add_parser("validate", help="validate a paper plan")
    val.add_argument("item_id", nargs="?", default="last")
    subm = cmd.add_parser("submit", help="submit a paper plan (simulated fills only)")
    subm.add_argument("item_id", nargs="?", default="last")
    subm.add_argument("--policy", default="base")
    subm.add_argument("--ledger", default="")
    fills = cmd.add_parser("fills", help="paper fills for a run")
    fills.add_argument("item_id", nargs="?", default="last")
    pos = cmd.add_parser("positions", help="paper positions")
    pos.add_argument("item_id", nargs="?", default="PAPER-001")
    cash = cmd.add_parser("cash", help="paper cash ledger")
    cash.add_argument("item_id", nargs="?", default="PAPER-001")
    rec = cmd.add_parser("reconcile", help="reconciliation report")
    rec.add_argument("item_id", nargs="?", default="last")
    orders = cmd.add_parser("orders", help="paper orders for a run")
    orders.add_argument("item_id", nargs="?", default="last")
    ev = cmd.add_parser("events", help="order events")
    ev.add_argument("item_id", nargs="?", default="")
    cancel = cmd.add_parser("cancel", help="cancel a paper order remainder")
    cancel.add_argument("item_id")
    rep = cmd.add_parser("report", help="paper OMS report")
    rep.add_argument("item_id", nargs="?", default="last")
    tca = cmd.add_parser("tca", help="paper TCA")
    tca.add_argument("item_id", nargs="?", default="last")
    res = cmd.add_parser("residuals", help="residual target quantities")
    res.add_argument("item_id", nargs="?", default="last")
    exc = cmd.add_parser("exceptions", help="paper exceptions")
    exc.add_argument("item_id", nargs="?", default="last")
    aud = cmd.add_parser("audit", help="paper audit trail")
    aud.add_argument("item_id", nargs="?", default="last")


def add_research_paper_parsers(research_sub: Any) -> None:
    for name, help_text in (
        ("paper-oms", "paper OMS overview"),
        ("paper-execution", "paper fills (simulated)"),
        ("order-lifecycle", "paper order states"),
        ("reconciliation", "paper reconciliation"),
        ("paper-tca", "paper transaction-cost analysis"),
    ):
        item = research_sub.add_parser(name, help=help_text)
        item.add_argument("item_id", nargs="?", default="last")
        item.add_argument("--ledger", default="")


def run_paper_command(args: Any) -> int:
    cmd = args.paper_cmd
    item = getattr(args, "item_id", "last")
    mapping: dict[str, Callable[[], Any]] = {
        "list": list_payload,
        "inspect": lambda: inspect_payload(item),
        "create": create_payload,
        "plan": lambda: plan_payload(item, policy=getattr(args, "policy", "base")),
        "validate": lambda: validate_payload(item),
        "submit": lambda: submit_payload(
            item, policy=getattr(args, "policy", "base"), ledger=getattr(args, "ledger", "")
        ),
        "fills": lambda: fills_payload(item),
        "positions": lambda: positions_payload(item),
        "cash": lambda: cash_payload(item),
        "reconcile": lambda: reconcile_payload(item),
        "orders": lambda: orders_payload(item),
        "events": lambda: events_payload(item),
        "cancel": lambda: cancel_payload(item),
        "report": lambda: report_payload(item),
        "tca": lambda: tca_payload(item),
        "residuals": lambda: residuals_payload(item),
        "exceptions": lambda: exceptions_payload(item),
        "audit": lambda: audit_payload(item),
    }
    print(json.dumps(mapping[cmd](), indent=2, default=str))
    return 0


def run_research_paper_command(args: Any) -> int:
    cmd = args.research_cmd
    item = getattr(args, "item_id", "last")
    if cmd == "paper-oms":
        print(json.dumps(list_payload(), indent=2, default=str))
    elif cmd == "paper-execution":
        print(json.dumps(fills_payload(item), indent=2, default=str))
    elif cmd == "order-lifecycle":
        print(json.dumps(orders_payload(item), indent=2, default=str))
    elif cmd == "reconciliation":
        print(json.dumps(reconcile_payload(item), indent=2, default=str))
    else:
        print(json.dumps(tca_payload(item), indent=2, default=str))
    return 0
