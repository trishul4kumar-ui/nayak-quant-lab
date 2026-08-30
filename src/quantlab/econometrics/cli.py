"""quantlab econometrics commands. Research only. No orders."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from quantlab.app.econometrics import (
    breaks_payload,
    causal_payload,
    cointegration_payload,
    dependence_payload,
    granger_payload,
    inspect_payload,
    list_payload,
    panel_payload,
    report_payload,
    residuals_payload,
    robustness_payload,
    run_payload,
    stationarity_payload,
    var_payload,
    vecm_payload,
)


def add_econometrics_parser(sub: Any) -> None:
    parser = sub.add_parser("econometrics", help="time-series / causal research (not a claim)")
    cmd = parser.add_subparsers(dest="econometrics_cmd", required=True)
    cmd.add_parser("list", help="list econometric runs")
    inspect_p = cmd.add_parser("inspect", help="inspect a run")
    inspect_p.add_argument("item_id", nargs="?", default="last")
    for name in (
        "stationarity",
        "dependence",
        "cointegration",
        "var",
        "vecm",
        "granger",
        "breaks",
        "panel",
        "causal",
        "residuals",
        "robustness",
        "report",
    ):
        item = cmd.add_parser(name, help=f"econometrics {name}")
        if name in {"stationarity", "dependence"}:
            item.add_argument("feature", nargs="?", default="seed")
        if name == "cointegration":
            item.add_argument("left", nargs="?", default="y")
            item.add_argument("right", nargs="?", default="x")
        if name == "granger":
            item.add_argument("x", nargs="?", default="x")
            item.add_argument("y", nargs="?", default="y")
        if name in {"var", "vecm", "breaks", "panel", "causal"}:
            item.add_argument("spec", nargs="?", default="seed-econo")
        if name in {"residuals", "robustness", "report"}:
            item.add_argument("experiment", nargs="?", default="last")
        item.add_argument("--ledger", default="")


def add_research_econometrics_parsers(research_sub: Any) -> None:
    for name, help_text in (
        ("econometrics", "econometric research engine"),
        ("stationarity", "ADF/KPSS diagnostics"),
        ("granger", "predictive Granger tests"),
        ("cointegration", "Engle-Granger residual ADF"),
        ("structural-break", "CUSUM / rolling stability"),
        ("causal", "causal interfaces with explicit assumptions"),
        ("panel", "pooled / FE / Fama-MacBeth research"),
    ):
        item = research_sub.add_parser(name, help=help_text)
        item.add_argument("item_id", nargs="?", default="last")
        item.add_argument("--ledger", default="")


def run_econometrics_command(args: Any) -> int:
    cmd = args.econometrics_cmd
    item = getattr(args, "item_id", "last")
    mapping: dict[str, Callable[[], Any]] = {
        "list": list_payload,
        "inspect": lambda: inspect_payload(item),
        "stationarity": stationarity_payload,
        "dependence": dependence_payload,
        "cointegration": cointegration_payload,
        "var": var_payload,
        "vecm": vecm_payload,
        "granger": granger_payload,
        "breaks": breaks_payload,
        "panel": panel_payload,
        "causal": causal_payload,
        "residuals": residuals_payload,
        "robustness": robustness_payload,
        "report": report_payload,
    }
    if cmd != "list" and cmd != "inspect":
        run_payload(ledger=getattr(args, "ledger", ""))
    print(json.dumps(mapping[cmd](), indent=2, default=str))
    return 0


def run_research_econometrics_command(args: Any) -> int:
    cmd = args.research_cmd
    run_payload(ledger=getattr(args, "ledger", ""))
    if cmd == "stationarity":
        print(json.dumps(stationarity_payload(), indent=2, default=str))
    elif cmd == "granger":
        print(json.dumps(granger_payload(), indent=2, default=str))
    elif cmd == "cointegration":
        print(json.dumps(cointegration_payload(), indent=2, default=str))
    elif cmd == "structural-break":
        print(json.dumps(breaks_payload(), indent=2, default=str))
    elif cmd == "causal":
        print(json.dumps(causal_payload(), indent=2, default=str))
    elif cmd == "panel":
        print(json.dumps(panel_payload(), indent=2, default=str))
    else:
        print(json.dumps(report_payload(), indent=2, default=str))
    return 0
