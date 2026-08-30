"""quantlab monitor commands. Observation only. No orders."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from quantlab.app.monitoring import (
    alpha_attribution_payload,
    attribution_payload,
    benchmark_payload,
    concentration_payload,
    drawdown_payload,
    drift_payload,
    exposure_payload,
    factor_attribution_payload,
    feedback_payload,
    inspect_payload,
    list_payload,
    performance_payload,
    pnl_payload,
    reconcile_payload,
    report_payload,
    returns_payload,
    risk_payload,
    run_payload,
    turnover_payload,
)


def add_monitor_parser(sub: Any) -> None:
    parser = sub.add_parser("monitor", help="portfolio monitoring / attribution (not a backtester)")
    cmd = parser.add_subparsers(dest="monitor_cmd", required=True)
    cmd.add_parser("list", help="list monitoring runs")
    inspect_p = cmd.add_parser("inspect", help="inspect a monitoring run")
    inspect_p.add_argument("item_id", nargs="?", default="last")
    run_p = cmd.add_parser("run", help="run monitoring on the last paper OMS result")
    run_p.add_argument("--ledger", default="")
    for name in (
        "performance",
        "pnl",
        "returns",
        "attribution",
        "factor-attribution",
        "alpha-attribution",
        "exposure",
        "drift",
        "drawdown",
        "concentration",
        "turnover",
        "benchmark",
        "risk",
        "feedback",
        "reconcile",
        "report",
    ):
        cmd.add_parser(name, help=f"monitoring {name}")


def add_research_monitor_parsers(research_sub: Any) -> None:
    for name, help_text in (
        ("performance", "post-decision performance"),
        ("attribution", "P&L attribution"),
        ("portfolio-drift", "target vs observed drift"),
        ("performance-feedback", "research feedback from performance"),
    ):
        item = research_sub.add_parser(name, help=help_text)
        item.add_argument("item_id", nargs="?", default="last")
        item.add_argument("--ledger", default="")


def run_monitor_command(args: Any) -> int:
    cmd = args.monitor_cmd
    item = getattr(args, "item_id", "last")
    mapping: dict[str, Callable[[], Any]] = {
        "list": list_payload,
        "inspect": lambda: inspect_payload(item),
        "run": lambda: run_payload(ledger=getattr(args, "ledger", "")),
        "performance": performance_payload,
        "pnl": pnl_payload,
        "returns": returns_payload,
        "attribution": attribution_payload,
        "factor-attribution": factor_attribution_payload,
        "alpha-attribution": alpha_attribution_payload,
        "exposure": exposure_payload,
        "drift": drift_payload,
        "drawdown": drawdown_payload,
        "concentration": concentration_payload,
        "turnover": turnover_payload,
        "benchmark": benchmark_payload,
        "risk": risk_payload,
        "feedback": feedback_payload,
        "reconcile": reconcile_payload,
        "report": report_payload,
    }
    print(json.dumps(mapping[cmd](), indent=2, default=str))
    return 0


def run_research_monitor_command(args: Any) -> int:
    cmd = args.research_cmd
    if cmd == "performance":
        print(json.dumps(performance_payload(), indent=2, default=str))
    elif cmd == "attribution":
        print(json.dumps(attribution_payload(), indent=2, default=str))
    elif cmd == "portfolio-drift":
        print(json.dumps(drift_payload(), indent=2, default=str))
    else:
        print(json.dumps(feedback_payload(), indent=2, default=str))
    return 0
