"""quantlab tca commands. Research/calibration only. No routing."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from quantlab.app.tca import (
    calibrate_payload,
    calibration_report_payload,
    capacity_payload,
    compare_payload,
    costs_payload,
    fragility_payload,
    impact_payload,
    inspect_payload,
    latency_payload,
    liquidity_payload,
    list_payload,
    report_payload,
    run_payload,
    sensitivity_payload,
    shortfall_payload,
    slippage_payload,
    spread_payload,
    stress_payload,
)


def add_tca_parser(sub: Any) -> None:
    parser = sub.add_parser("tca", help="transaction cost analysis / capacity (not live)")
    cmd = parser.add_subparsers(dest="tca_cmd", required=True)
    cmd.add_parser("list", help="list TCA runs")
    inspect_p = cmd.add_parser("inspect", help="inspect a TCA run")
    inspect_p.add_argument("item_id", nargs="?", default="last")
    run_p = cmd.add_parser("run", help="run TCA on the last paper OMS result")
    run_p.add_argument("--ledger", default="")
    for name in (
        "spread",
        "slippage",
        "impact",
        "shortfall",
        "costs",
        "latency",
        "liquidity",
        "calibrate",
        "calibration-report",
        "capacity",
        "fragility",
        "sensitivity",
        "stress",
        "compare",
        "report",
    ):
        item = cmd.add_parser(name, help=f"tca {name}")
        if name in {"run", "calibrate"}:
            item.add_argument("--ledger", default="")


def add_research_tca_parsers(research_sub: Any) -> None:
    for name, help_text in (
        ("tca", "transaction cost analysis"),
        ("implementation-shortfall", "implementation shortfall"),
        ("execution-calibration", "PIT execution calibration"),
        ("tca-capacity", "policy-defined capacity (not Prompt 13 capacity)"),
        ("tca-fragility", "execution fragility from TCA"),
    ):
        item = research_sub.add_parser(name, help=help_text)
        item.add_argument("item_id", nargs="?", default="last")
        item.add_argument("--ledger", default="")


def run_tca_command(args: Any) -> int:
    cmd = args.tca_cmd
    item = getattr(args, "item_id", "last")
    mapping: dict[str, Callable[[], Any]] = {
        "list": list_payload,
        "inspect": lambda: inspect_payload(item),
        "run": lambda: run_payload(ledger=getattr(args, "ledger", "")),
        "spread": spread_payload,
        "slippage": slippage_payload,
        "impact": impact_payload,
        "shortfall": shortfall_payload,
        "costs": costs_payload,
        "latency": latency_payload,
        "liquidity": liquidity_payload,
        "calibrate": lambda: calibrate_payload(ledger=getattr(args, "ledger", "")),
        "calibration-report": calibration_report_payload,
        "capacity": capacity_payload,
        "fragility": fragility_payload,
        "sensitivity": sensitivity_payload,
        "stress": stress_payload,
        "compare": compare_payload,
        "report": report_payload,
    }
    print(json.dumps(mapping[cmd](), indent=2, default=str))
    return 0


def run_research_tca_command(args: Any) -> int:
    cmd = args.research_cmd
    if cmd == "implementation-shortfall":
        print(json.dumps(shortfall_payload(), indent=2, default=str))
    elif cmd == "execution-calibration":
        print(json.dumps(calibrate_payload(), indent=2, default=str))
    elif cmd == "tca-capacity":
        print(json.dumps(capacity_payload(), indent=2, default=str))
    elif cmd == "tca-fragility":
        print(json.dumps(fragility_payload(), indent=2, default=str))
    else:
        print(json.dumps(report_payload(), indent=2, default=str))
    return 0
