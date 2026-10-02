"""CLI reporting surface for reconciliation evidence. No trade controls."""

from __future__ import annotations

import json
from typing import Any

from quantlab.broker_gateway.service import last_snapshot, matching_internal_books
from quantlab.reconciliation.models import ExceptionStatus
from quantlab.reconciliation.repository import audit, exceptions, history, last
from quantlab.reconciliation.service import internal_from_books, reconcile, transition_exception


def add_reconciliation_parser(sub: Any) -> None:
    parser = sub.add_parser("reconcile", help="audit broker versus internal account state")
    cmd = parser.add_subparsers(dest="reconcile_cmd", required=True)
    for name in (
        "run",
        "status",
        "account",
        "positions",
        "orders",
        "fills",
        "cash",
        "exceptions",
        "history",
        "report",
        "audit",
    ):
        cmd.add_parser(name, help=f"reconciliation {name}")
    transition = cmd.add_parser("transition", help="advance an exception workflow state")
    transition.add_argument("exception_id")
    transition.add_argument("status", choices=[item.value for item in ExceptionStatus])


def run_reconciliation_command(args: Any) -> int:
    command = args.reconcile_cmd
    if command == "run":
        broker = last_snapshot()
        if broker is None:
            from quantlab.broker_gateway.service import snapshot

            broker = snapshot()
        report = reconcile(
            broker,
            internal_from_books(
                matching_internal_books(), observed_at=broker.provenance.source_timestamp
            ),
        )
        payload: object = report.model_dump(mode="json")
    elif command == "transition":
        item = next((row for row in exceptions() if row.exception_id == args.exception_id), None)
        if item is None:
            raise SystemExit(f"unknown reconciliation exception: {args.exception_id}")
        payload = transition_exception(item, ExceptionStatus(args.status)).model_dump(mode="json")
    else:
        last_report = last()
        if command == "status":
            payload = {
                "status": last_report.status.value if last_report else "UNKNOWN",
                "live_trading": False,
                "write_enabled": False,
            }
        elif command == "exceptions":
            payload = [item.model_dump(mode="json") for item in exceptions()]
        elif command == "history":
            payload = [item.model_dump(mode="json") for item in history()]
        elif command == "audit":
            payload = audit()
        elif command in {"account", "cash", "positions", "orders", "fills"}:
            payload = (
                [
                    item.model_dump(mode="json")
                    for item in last_report.exceptions
                    if item.dimension
                    in {
                        command,
                        "position" if command == "positions" else command,
                        "order" if command == "orders" else command,
                        "fill" if command == "fills" else command,
                    }
                ]
                if last_report
                else []
            )
        else:
            payload = (
                last_report.model_dump(mode="json")
                if last_report
                else {"status": "UNKNOWN", "note": "No reconciliation report."}
            )
    print(json.dumps(payload, indent=2, default=str))
    return 0
