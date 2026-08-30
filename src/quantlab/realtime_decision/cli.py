"""quantlab realtime-decision — decision ≠ order."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from quantlab.app.realtime_decision import (
    abstentions_payload,
    audit_payload,
    explain_payload,
    exposure_payload,
    inspect_payload,
    lineage_payload,
    portfolio_payload,
    releases_payload,
    replay_payload,
    risk_payload,
    run_payload,
    status_payload,
)


def add_realtime_decision_parser(sub: Any) -> None:
    parser = sub.add_parser(
        "realtime-decision",
        help="real-time research-to-decision engine (not an OMS)",
    )
    cmd = parser.add_subparsers(dest="realtime_decision_cmd", required=True)
    cmd.add_parser("status", help="decision-cycle status")
    cmd.add_parser("releases", help="bound strategy releases")
    inspect_p = cmd.add_parser("inspect", help="inspect a decision")
    inspect_p.add_argument("item_id", nargs="?", default="last")
    run_p = cmd.add_parser("run", help="run one decision cycle")
    run_p.add_argument("--release", default="default", help="default|research")
    cmd.add_parser("explain", help="explain last decision")
    cmd.add_parser("abstentions", help="abstention reasons")
    cmd.add_parser("risk", help="risk posture")
    cmd.add_parser("exposure", help="target exposure")
    cmd.add_parser("portfolio", help="target portfolio (not an order)")
    cmd.add_parser("replay", help="replay last decision")
    cmd.add_parser("audit", help="audit trail")
    cmd.add_parser("lineage", help="snapshot→decision lineage")


def add_research_realtime_decision_parsers(research_sub: Any) -> None:
    for name, help_text in (
        ("realtime", "real-time decision cycle"),
        ("realtime-decision", "TargetPortfolio is not an order"),
        ("decision-replay", "replay a frozen decision"),
        ("decision-stability", "decision hash stability"),
        ("decision-abstention", "first-class abstention"),
    ):
        item = research_sub.add_parser(name, help=help_text)
        item.add_argument("item_id", nargs="?", default="last")
        item.add_argument("--ledger", default="")
        if name in {"realtime", "realtime-decision"}:
            item.add_argument("--release", default="default")


def run_realtime_decision_command(args: Any) -> int:
    cmd = args.realtime_decision_cmd
    item = getattr(args, "item_id", "last")
    release = getattr(args, "release", "default")
    mapping: dict[str, Callable[[], Any]] = {
        "status": status_payload,
        "releases": releases_payload,
        "inspect": lambda: inspect_payload(item),
        "run": lambda: run_payload(release),
        "explain": explain_payload,
        "abstentions": abstentions_payload,
        "risk": risk_payload,
        "exposure": exposure_payload,
        "portfolio": portfolio_payload,
        "replay": replay_payload,
        "audit": audit_payload,
        "lineage": lineage_payload,
    }
    print(json.dumps(mapping[cmd](), indent=2, default=str))
    return 0


def run_research_realtime_decision_command(args: Any) -> int:
    cmd = args.research_cmd
    item = getattr(args, "item_id", "last")
    release = getattr(args, "release", "default")
    if cmd in {"realtime", "realtime-decision"}:
        payload: Any = run_payload(release)
    elif cmd == "decision-replay" or cmd == "decision-stability":
        payload = replay_payload()
    elif cmd == "decision-abstention":
        payload = abstentions_payload()
    else:
        payload = inspect_payload(item)
    print(json.dumps(payload, indent=2, default=str))
    return 0
