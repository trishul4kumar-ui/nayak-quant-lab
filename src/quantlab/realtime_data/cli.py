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
