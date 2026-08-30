"""quantlab capital commands. Allocation and decisions; not orders."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from quantlab.app.capital import (
    abstentions_payload,
    allocate_named,
    compare_payload,
    constraints_payload,
    decision_payload,
    drawdown_payload,
    explain_payload,
    exposure_payload,
    inspect_payload,
    lineage_payload,
    liquidity_payload,
    list_payload,
    report_payload,
    risk_payload,
    sizing_payload,
    turnover_payload,
    validate_payload,
)


def add_capital_parser(sub: Any) -> None:
    parser = sub.add_parser("capital", help="capital allocation / investment decisions")
    cmd = parser.add_subparsers(dest="capital_cmd", required=True)
    cmd.add_parser("list", help="list capital policies")
    inspect_p = cmd.add_parser("inspect", help="inspect a capital policy")
    inspect_p.add_argument("item_id", nargs="?", default="CAP-RESEARCH-001")
    validate_p = cmd.add_parser("validate", help="validate a capital policy")
    validate_p.add_argument("item_id", nargs="?", default="CAP-RESEARCH-001")
    alloc = cmd.add_parser("allocate", help="allocate research capital to a seed portfolio")
    alloc.add_argument("item_id", nargs="?", default="mom20_topn")
    alloc.add_argument("--ledger", default="")
    dec = cmd.add_parser("decision", help="inspect an investment decision")
    dec.add_argument("item_id", nargs="?", default="last")
    exp = cmd.add_parser("explain", help="explain an investment decision")
    exp.add_argument("item_id", nargs="?", default="last")
    con = cmd.add_parser("constraints", help="constraint status for a decision")
    con.add_argument("item_id", nargs="?", default="last")
    risk = cmd.add_parser("risk", help="risk view for a decision")
    risk.add_argument("item_id", nargs="?", default="last")
    expo = cmd.add_parser("exposure", help="factor/beta exposure for a decision")
    expo.add_argument("item_id", nargs="?", default="last")
    siz = cmd.add_parser("sizing", help="sizing method used")
    siz.add_argument("item_id", nargs="?", default="last")
    turn = cmd.add_parser("turnover", help="turnover estimate")
    turn.add_argument("item_id", nargs="?", default="last")
    liq = cmd.add_parser("liquidity", help="liquidity status")
    liq.add_argument("item_id", nargs="?", default="last")
    dd = cmd.add_parser("drawdown", help="drawdown capital state")
    dd.add_argument("item_id", nargs="?", default="last")
    cmp_p = cmd.add_parser("compare", help="compare two decisions")
    cmp_p.add_argument("decision_a", nargs="?", default="last")
    cmp_p.add_argument("decision_b", nargs="?", default="last")
    lin = cmd.add_parser("lineage", help="decision lineage identifiers")
    lin.add_argument("item_id", nargs="?", default="last")
    cmd.add_parser("abstentions", help="list abstentions")
    rep = cmd.add_parser("report", help="capital decision report")
    rep.add_argument("item_id", nargs="?", default="last")


def add_research_capital_parsers(research_sub: Any) -> None:
    for name, help_text in (
        ("capital", "capital allocation overview"),
        ("allocation", "last target weights"),
        ("decision", "last investment decision"),
        ("risk-budget", "risk view of last allocation"),
        ("sizing", "sizing method of last allocation"),
        ("capital-efficiency", "capital efficiency diagnostics"),
        ("allocation-stability", "allocation stability diagnostics"),
    ):
        item = research_sub.add_parser(name, help=help_text)
        item.add_argument("item_id", nargs="?", default="last")
        item.add_argument("--ledger", default="")


def run_capital_command(args: Any) -> int:
    cmd = args.capital_cmd
    item = getattr(args, "item_id", "last")
    mapping: dict[str, Callable[[], Any]] = {
        "list": list_payload,
        "inspect": lambda: inspect_payload(item),
        "validate": lambda: validate_payload(item),
        "allocate": lambda: allocate_named(item, ledger=getattr(args, "ledger", "")),
        "decision": lambda: decision_payload(item),
        "explain": lambda: explain_payload(item),
        "constraints": lambda: constraints_payload(item),
        "risk": lambda: risk_payload(item),
        "exposure": lambda: exposure_payload(item),
        "sizing": lambda: sizing_payload(item),
        "turnover": lambda: turnover_payload(item),
        "liquidity": lambda: liquidity_payload(item),
        "drawdown": lambda: drawdown_payload(item),
        "compare": lambda: compare_payload(
            getattr(args, "decision_a", "last"), getattr(args, "decision_b", "last")
        ),
        "lineage": lambda: lineage_payload(item),
        "abstentions": abstentions_payload,
        "report": lambda: report_payload(item),
    }
    action = mapping[cmd]
    print(json.dumps(action(), indent=2, default=str))
    return 0


def run_research_capital_command(args: Any) -> int:
    cmd = args.research_cmd
    item = getattr(args, "item_id", "last")
    if cmd == "capital":
        print(json.dumps(list_payload(), indent=2, default=str))
    elif cmd == "allocation" or cmd == "decision":
        print(json.dumps(decision_payload(item), indent=2, default=str))
    elif cmd == "risk-budget":
        print(json.dumps(risk_payload(item), indent=2, default=str))
    elif cmd == "sizing":
        print(json.dumps(sizing_payload(item), indent=2, default=str))
    elif cmd == "capital-efficiency":
        print(json.dumps(report_payload(item), indent=2, default=str))
    else:
        print(json.dumps(report_payload(item), indent=2, default=str))
    return 0
