"""quantlab broker — read-only account gateway. Not order routing."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from quantlab.app.broker_gateway import (
    account_payload,
    audit_payload,
    connect_payload,
    disconnect_payload,
    fills_payload,
    health_payload,
    holdings_payload,
    incidents_payload,
    inspect_payload,
    list_payload,
    mappings_payload,
    margins_payload,
    orders_payload,
    positions_payload,
    profile_payload,
    reconcile_payload,
    snapshot_payload,
    trades_payload,
)


def add_broker_parser(sub: Any) -> None:
    parser = sub.add_parser("broker", help="read-only broker/account gateway (not live)")
    cmd = parser.add_subparsers(dest="broker_cmd", required=True)
    cmd.add_parser("list", help="list snapshots")
    inspect_p = cmd.add_parser("inspect", help="inspect a snapshot")
    inspect_p.add_argument("item_id", nargs="?", default="last")
    cmd.add_parser("health", help="connection health")
    connect_p = cmd.add_parser("connect", help="connect a read-only account adapter")
    connect_p.add_argument("--scenario", default="normal")
    connect_p.add_argument("--adapter", choices=("mock", "kite"), default="mock")
    cmd.add_parser("disconnect", help="disconnect")
    cmd.add_parser("account", help="account snapshot")
    cmd.add_parser("profile", help="sanitized account profile")
    cmd.add_parser("positions", help="positions")
    cmd.add_parser("holdings", help="holdings")
    cmd.add_parser("margins", help="margins")
    cmd.add_parser("orders", help="orders (read-only)")
    cmd.add_parser("fills", help="fills (read-only)")
    cmd.add_parser("trades", help="trades (read-only)")
    cmd.add_parser("snapshot", help="immutable snapshot")
    cmd.add_parser("reconcile", help="three-way reconciliation")
    cmd.add_parser("audit", help="audit trail")
    cmd.add_parser("incidents", help="gateway incidents")
    cmd.add_parser("mappings", help="instrument mappings")


def add_research_broker_parsers(research_sub: Any) -> None:
    for name, help_text in (
        ("broker", "read-only broker gateway (not order routing)"),
        ("account-state", "canonical account snapshot"),
        ("account-reconciliation", "broker vs internal reconciliation"),
        ("broker-health", "broker connection health"),
        ("broker-audit", "broker gateway audit"),
    ):
        item = research_sub.add_parser(name, help=help_text)
        item.add_argument("item_id", nargs="?", default="last")
        item.add_argument("--ledger", default="")


def run_broker_command(args: Any) -> int:
    cmd = args.broker_cmd
    item = getattr(args, "item_id", "last")
    scenario = getattr(args, "scenario", "normal")
    adapter = getattr(args, "adapter", "mock")
    mapping: dict[str, Callable[[], Any]] = {
        "list": list_payload,
        "inspect": lambda: inspect_payload(item),
        "health": health_payload,
        "connect": lambda: connect_payload(scenario, adapter=adapter),
        "disconnect": disconnect_payload,
        "account": account_payload,
        "profile": profile_payload,
        "positions": positions_payload,
        "holdings": holdings_payload,
        "margins": margins_payload,
        "orders": orders_payload,
        "fills": fills_payload,
        "trades": trades_payload,
        "snapshot": snapshot_payload,
        "reconcile": reconcile_payload,
        "audit": audit_payload,
        "incidents": incidents_payload,
        "mappings": mappings_payload,
    }
    print(json.dumps(mapping[cmd](), indent=2, default=str))
    return 0


def run_research_broker_command(args: Any) -> int:
    cmd = args.research_cmd
    item = getattr(args, "item_id", "last")
    if cmd == "account-state":
        payload: Any = account_payload()
    elif cmd == "account-reconciliation":
        payload = reconcile_payload()
    elif cmd == "broker-health":
        payload = health_payload()
    elif cmd == "broker-audit":
        payload = audit_payload()
    else:
        payload = inspect_payload(item)
    print(json.dumps(payload, indent=2, default=str))
    return 0
