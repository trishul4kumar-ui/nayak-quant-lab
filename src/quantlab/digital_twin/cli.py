"""quantlab twin — deterministic shadow / replay. Not Prompt 24 shadow."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from quantlab.app.digital_twin import (
    audit_payload,
    checkpoint_payload,
    compare_payload,
    counterfactual_payload,
    create_payload,
    determinism_payload,
    failures_payload,
    halt_payload,
    inspect_payload,
    list_payload,
    pause_payload,
    reconcile_payload,
    recovery_payload,
    replay_payload,
    report_payload,
    run_payload,
)


def add_twin_parser(sub: Any) -> None:
    parser = sub.add_parser(
        "twin",
        help="deterministic shadow validation / replay digital twin (not live)",
    )
    cmd = parser.add_subparsers(dest="twin_cmd", required=True)
    cmd.add_parser("list", help="list twin runs")
    inspect_p = cmd.add_parser("inspect", help="inspect a run")
    inspect_p.add_argument("item_id", nargs="?", default="last")
    create_p = cmd.add_parser("create", help="create a twin run")
    create_p.add_argument("--mode", default="determinism_test")
    run_p = cmd.add_parser("run", help="run a twin cycle")
    run_p.add_argument("--mode", default="determinism_test")
    cmd.add_parser("pause", help="pause (no broker effect)")
    cmd.add_parser("halt", help="halt the twin")
    cmd.add_parser("checkpoint", help="write a checkpoint")
    cmd.add_parser("replay", help="replay a run")
    cmd.add_parser("compare", help="compare original vs replay")
    cmd.add_parser("reconcile", help="reconciliation status")
    fail_p = cmd.add_parser("failures", help="inject a controlled failure")
    fail_p.add_argument("--kind", default="stale_market")
    cmd.add_parser("recovery", help="restore from checkpoint")
    cmd.add_parser("determinism", help="determinism test")
    cmd.add_parser("counterfactual", help="labelled counterfactual")
    cmd.add_parser("report", help="twin report")
    cmd.add_parser("audit", help="audit trail")


def add_research_twin_parsers(research_sub: Any) -> None:
    for name, help_text in (
        ("digital-twin", "deterministic shadow / replay twin"),
        ("twin-validation", "shadow validation (not Prompt 24)"),
        ("deterministic-replay", "replay identity"),
        ("failure-injection", "controlled failure injection"),
        ("twin-recovery", "checkpoint recovery"),
        ("counterfactual", "labelled counterfactual"),
        ("twin-drift", "twin vs observed drift"),
    ):
        item = research_sub.add_parser(name, help=help_text)
        item.add_argument("item_id", nargs="?", default="last")
        item.add_argument("--ledger", default="")
        if name == "failure-injection":
            item.add_argument("--kind", default="stale_market")


def run_twin_command(args: Any) -> int:
    cmd = args.twin_cmd
    item = getattr(args, "item_id", "last")
    mode = getattr(args, "mode", "determinism_test")
    kind = getattr(args, "kind", "stale_market")
    mapping: dict[str, Callable[[], Any]] = {
        "list": list_payload,
        "inspect": lambda: inspect_payload(item),
        "create": lambda: create_payload(mode),
        "run": lambda: run_payload(mode),
        "pause": pause_payload,
        "halt": halt_payload,
        "checkpoint": checkpoint_payload,
        "replay": replay_payload,
        "compare": compare_payload,
        "reconcile": reconcile_payload,
        "failures": lambda: failures_payload(kind),
        "recovery": recovery_payload,
        "determinism": determinism_payload,
        "counterfactual": counterfactual_payload,
        "report": report_payload,
        "audit": audit_payload,
    }
    print(json.dumps(mapping[cmd](), indent=2, default=str))
    return 0


def run_research_twin_command(args: Any) -> int:
    cmd = args.research_cmd
    item = getattr(args, "item_id", "last")
    kind = getattr(args, "kind", "stale_market")
    if cmd == "failure-injection":
        payload: Any = failures_payload(kind)
    elif cmd == "deterministic-replay":
        payload = replay_payload()
    elif cmd == "twin-recovery":
        payload = recovery_payload()
    elif cmd == "counterfactual":
        payload = counterfactual_payload()
    elif cmd == "twin-drift":
        payload = compare_payload()
    elif cmd == "twin-validation":
        payload = run_payload("determinism_test")
    else:
        payload = inspect_payload(item)
    print(json.dumps(payload, indent=2, default=str))
    return 0
