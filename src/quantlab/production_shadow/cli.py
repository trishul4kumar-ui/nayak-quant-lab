"""CLI for non-routable production-shadow evidence."""

from __future__ import annotations

import json
from typing import Any

from quantlab.production_shadow.repository import audit, last, state
from quantlab.production_shadow.service import assess, start, stop


def add_production_shadow_parser(sub: Any) -> None:
    parser = sub.add_parser(
        "shadow-prod", help="production-shadow evidence only; no broker routing"
    )
    cmd = parser.add_subparsers(dest="production_shadow_cmd", required=True)
    for name in (
        "status",
        "start",
        "stop",
        "run",
        "health",
        "decisions",
        "orders",
        "fills",
        "drift",
        "reconciliation",
        "incidents",
        "readiness",
        "replay",
        "audit",
        "report",
    ):
        cmd.add_parser(name, help=f"production shadow {name}")


def run_production_shadow_command(args: Any) -> int:
    command = args.production_shadow_cmd
    if command == "start":
        payload: object = {"state": start().value, "live_trading": False}
    elif command == "stop":
        payload = {"state": stop().value, "live_trading": False}
    elif command == "run":
        payload = assess().model_dump(mode="json")
    elif command == "status":
        item = last()
        payload = {
            "state": state(),
            "last_run": item.model_dump(mode="json") if item else None,
            "live_trading": False,
        }
    elif command == "audit":
        payload = audit()
    else:
        item = last()
        if command == "incidents":
            payload = [row.model_dump(mode="json") for row in item.incidents] if item else []
        elif command == "readiness":
            payload = item.readiness.model_dump(mode="json") if item else {"note": "NOT_TESTED"}
        elif command == "report":
            payload = (
                item.model_dump(mode="json") if item else {"note": "No production-shadow run."}
            )
        elif command == "health":
            payload = {
                "state": state(),
                "blocked": bool(item and item.readiness.critical_failures),
                "live_trading": False,
            }
        else:
            payload = item.model_dump(mode="json") if item else {"note": "NOT_TESTED"}
    print(json.dumps(payload, indent=2, default=str))
    return 0
