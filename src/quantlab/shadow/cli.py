"""quantlab shadow commands. Paper/shadow only. No broker routing."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from quantlab.app.shadow import (
    audit_payload,
    cash_payload,
    checkpoint_payload,
    compare_payload,
    cycle_payload,
    decision_payload,
    drift_payload,
    fills_payload,
    health_payload,
    incidents_payload,
    inspect_payload,
    latency_payload,
    list_payload,
    orders_payload,
    pause_payload,
    positions_payload,
    reconcile_payload,
    recover_payload,
    replay_payload,
    report_payload,
    resume_payload,
    run_payload,
    start_payload,
    status_payload,
    stop_payload,
    targets_payload,
    tca_payload,
)


def add_shadow_parser(sub: Any) -> None:
    parser = sub.add_parser(
        "shadow",
        help="production paper / shadow execution (not live, not a broker)",
    )
    cmd = parser.add_subparsers(dest="shadow_cmd", required=True)
    cmd.add_parser("list", help="list shadow cycles")
    inspect_p = cmd.add_parser("inspect", help="inspect a shadow cycle")
    inspect_p.add_argument("item_id", nargs="?", default="last")
    start_p = cmd.add_parser("start", help="start the shadow engine (not live)")
    start_p.add_argument("--mode", default="research_paper")
    cmd.add_parser("stop", help="stop the shadow engine")
    cmd.add_parser("pause", help="pause new decisions")
    resume_p = cmd.add_parser("resume", help="resume from pause/recovery")
    resume_p.add_argument("--mode", default="research_paper")
    cmd.add_parser("status", help="engine status / heartbeat")
    run_p = cmd.add_parser("run", help="run one paper/shadow cycle")
    run_p.add_argument(
        "--mode",
        default="research_paper",
        choices=["research_paper", "paper", "shadow"],
    )
    run_p.add_argument("--ledger", default="")
    cyc = cmd.add_parser("cycle", help="last cycle identity")
    cyc.add_argument("item_id", nargs="?", default="last")
    for name in (
        "decision",
        "targets",
        "orders",
        "fills",
        "positions",
        "cash",
        "reconcile",
        "health",
        "incidents",
        "latency",
        "drift",
        "tca",
        "compare",
        "checkpoint",
        "audit",
        "report",
    ):
        item = cmd.add_parser(name, help=f"shadow {name}")
        if name not in {"health", "incidents"}:
            item.add_argument("item_id", nargs="?", default="last")
    rec = cmd.add_parser("recover", help="restore from checkpoint")
    rec.add_argument("--ledger", default="")
    replay_p = cmd.add_parser("replay", help="replay a frozen cycle")
    replay_p.add_argument("item_id", nargs="?", default="last")


def add_research_shadow_parsers(research_sub: Any) -> None:
    for name, help_text in (
        ("shadow", "production paper / shadow engine"),
        ("paper-production", "production-like paper cycle"),
        ("shadow-execution", "hypothetical shadow orders"),
        ("decision-drift", "paper vs shadow decision drift"),
        ("production-fragility", "production readiness scorecard"),
        ("shadow-tca", "shadow TCA wrap (not observed broker TCA)"),
        ("shadow-reconciliation", "shadow reconciliation"),
    ):
        item = research_sub.add_parser(name, help=help_text)
        item.add_argument("item_id", nargs="?", default="last")
        item.add_argument("--ledger", default="")
        if name in {"shadow", "paper-production", "shadow-execution"}:
            item.add_argument("--mode", default="research_paper")


def run_shadow_command(args: Any) -> int:
    cmd = args.shadow_cmd
    item = getattr(args, "item_id", "last")
    mode = getattr(args, "mode", "research_paper")
    ledger = getattr(args, "ledger", "")
    mapping: dict[str, Callable[[], Any]] = {
        "list": list_payload,
        "inspect": lambda: inspect_payload(item),
        "start": lambda: start_payload(mode=mode),
        "stop": stop_payload,
        "pause": pause_payload,
        "resume": lambda: resume_payload(mode=mode),
        "status": status_payload,
        "run": lambda: run_payload(mode=mode, ledger=ledger),
        "cycle": lambda: cycle_payload(item),
        "decision": lambda: decision_payload(item),
        "targets": lambda: targets_payload(item),
        "orders": lambda: orders_payload(item),
        "fills": lambda: fills_payload(item),
        "positions": lambda: positions_payload(item),
        "cash": lambda: cash_payload(item),
        "reconcile": lambda: reconcile_payload(item),
        "health": health_payload,
        "incidents": incidents_payload,
        "latency": lambda: latency_payload(item),
        "drift": lambda: drift_payload(item),
        "tca": lambda: tca_payload(item),
        "compare": lambda: compare_payload(item),
        "checkpoint": lambda: checkpoint_payload(item),
        "recover": recover_payload,
        "audit": lambda: audit_payload(item),
        "report": lambda: report_payload(item),
        "replay": lambda: replay_payload(item),
    }
    print(json.dumps(mapping[cmd](), indent=2, default=str))
    return 0


def run_research_shadow_command(args: Any) -> int:
    cmd = args.research_cmd
    item = getattr(args, "item_id", "last")
    ledger = getattr(args, "ledger", "")
    mode = getattr(args, "mode", "research_paper")
    if cmd == "paper-production":
        print(json.dumps(run_payload(mode="paper", ledger=ledger), indent=2, default=str))
    elif cmd == "shadow-execution":
        print(json.dumps(run_payload(mode="shadow", ledger=ledger), indent=2, default=str))
    elif cmd == "decision-drift":
        print(json.dumps(drift_payload(item), indent=2, default=str))
    elif cmd == "production-fragility":
        print(json.dumps(health_payload(), indent=2, default=str))
    elif cmd == "shadow-tca":
        print(json.dumps(tca_payload(item), indent=2, default=str))
    elif cmd == "shadow-reconciliation":
        print(json.dumps(reconcile_payload(item), indent=2, default=str))
    else:
        print(json.dumps(run_payload(mode=mode, ledger=ledger), indent=2, default=str))
    return 0
