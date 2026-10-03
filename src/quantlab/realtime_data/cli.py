"""quantlab realtime — observe-only market-data gateway."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from quantlab.app.realtime_data import (
    audit_payload,
    clock_payload,
    freshness_payload,
    health_payload,
    inspect_payload,
    quality_payload,
    replay_payload,
    sequence_payload,
    session_payload,
    snapshot_payload,
    sources_payload,
    start_payload,
    status_payload,
    stop_payload,
)
from quantlab.realtime_data.errors import RealTimeDataError
from quantlab.realtime_data.kite_auth import authenticate_locally


def add_realtime_parser(sub: Any) -> None:
    parser = sub.add_parser("realtime", help="observe-only real-time market-data gateway")
    cmd = parser.add_subparsers(dest="realtime_cmd", required=True)
    cmd.add_parser("health", help="feed health")
    cmd.add_parser("status", help="connection status")
    cmd.add_parser("sources", help="adapter sources")
    start_p = cmd.add_parser("start", help="start mock adapter")
    start_p.add_argument("--scenario", default="normal")
    cmd.add_parser("stop", help="stop adapter")
    cmd.add_parser("snapshot", help="freeze MarketState(T)")
    inspect_p = cmd.add_parser("inspect", help="inspect a snapshot")
    inspect_p.add_argument("item_id", nargs="?", default="last")
    cmd.add_parser("quality", help="data quality")
    cmd.add_parser("freshness", help="freshness")
    cmd.add_parser("sequence", help="sequence integrity")
    cmd.add_parser("clock", help="clock health")
    cmd.add_parser("session", help="session state")
    cmd.add_parser("replay", help="replay frozen observations")
    cmd.add_parser("audit", help="audit trail")


def add_market_data_parser(sub: Any) -> None:
    """Prompt 34 naming surface over the one real-time gateway."""
    parser = sub.add_parser("market-data", help="production-capable observe-only market data")
    cmd = parser.add_subparsers(dest="market_data_cmd", required=True)
    connect = cmd.add_parser("connect", help="connect configured production adapter")
    connect.add_argument("--adapter", choices=("kite", "production", "mock"), default="production")
    cmd.add_parser(
        "kite-login",
        help="open local Kite login and store a read-only access token",
    )
    for name in (
        "disconnect",
        "status",
        "sources",
        "health",
        "latency",
        "quality",
        "coverage",
        "instruments",
        "snapshot",
        "audit",
        "replay",
    ):
        item = cmd.add_parser(name, help=f"market-data {name}")
        if name == "snapshot":
            item.add_argument("--adapter", choices=("kite", "production", "mock"), default=None)


def add_research_realtime_parsers(research_sub: Any) -> None:
    for name, help_text in (
        ("realtime-data", "observe-only real-time market data"),
        ("market-state", "frozen MarketState(T)"),
        ("data-freshness", "observation freshness"),
        ("sequence-integrity", "sequence gaps and duplicates"),
        ("realtime-replay", "replay frozen observations"),
    ):
        item = research_sub.add_parser(name, help=help_text)
        item.add_argument("item_id", nargs="?", default="last")
        item.add_argument("--ledger", default="")


def run_realtime_command(args: Any) -> int:
    cmd = args.realtime_cmd
    item = getattr(args, "item_id", "last")
    scenario = getattr(args, "scenario", "normal")
    mapping: dict[str, Callable[[], Any]] = {
        "health": health_payload,
        "status": status_payload,
        "sources": sources_payload,
        "start": lambda: start_payload(scenario),
        "stop": stop_payload,
        "snapshot": snapshot_payload,
        "inspect": lambda: inspect_payload(item),
        "quality": quality_payload,
        "freshness": freshness_payload,
        "sequence": sequence_payload,
        "clock": clock_payload,
        "session": session_payload,
        "replay": replay_payload,
        "audit": audit_payload,
    }
    print(json.dumps(mapping[cmd](), indent=2, default=str))
    return 0


def run_market_data_command(args: Any) -> int:
    command = args.market_data_cmd
    if command == "kite-login":
        try:
            result = authenticate_locally()
            payload: Any = {
                "authenticated": True,
                "access_token_stored": True,
                "dotenv_path": str(result.dotenv_path),
                "live_trading": False,
                "observe_only": True,
            }
        except RealTimeDataError as exc:
            payload = {
                "error": str(exc),
                "live_trading": False,
                "observe_only": True,
            }
    elif command == "connect":
        payload = start_payload("normal", adapter=getattr(args, "adapter", "production"))
    elif command == "disconnect":
        payload = stop_payload()
    elif command == "status":
        payload = status_payload()
    elif command == "sources":
        payload = sources_payload()
    elif command == "health":
        payload = health_payload()
    elif command == "latency":
        health = health_payload()
        payload = {
            key: health.get(key)
            for key in ("event_to_receive_ms", "receive_to_process_ms", "process_to_snapshot_ms")
        }
    elif command == "quality":
        payload = quality_payload()
    elif command == "coverage":
        payload = {"coverage": health_payload().get("coverage"), "live_trading": False}
    elif command == "instruments":
        frozen = inspect_payload("last")
        payload = {"instruments": [row["security_id"] for row in frozen.get("observations", [])]}
    elif command == "snapshot":
        adapter = getattr(args, "adapter", None)
        if adapter is not None:
            started = start_payload("normal", adapter=adapter)
            payload = started if "error" in started else snapshot_payload()
        else:
            payload = snapshot_payload()
    elif command == "audit":
        payload = audit_payload()
    else:
        payload = replay_payload()
    print(json.dumps(payload, indent=2, default=str))
    return 0


def run_research_realtime_command(args: Any) -> int:
    cmd = args.research_cmd
    item = getattr(args, "item_id", "last")
    if cmd == "data-freshness":
        payload: Any = freshness_payload()
    elif cmd == "sequence-integrity":
        payload = sequence_payload()
    elif cmd == "realtime-replay":
        payload = replay_payload()
    elif cmd == "market-state":
        payload = snapshot_payload()
    else:
        payload = inspect_payload(item)
    print(json.dumps(payload, indent=2, default=str))
    return 0
