"""quantlab validation commands. Governance only. Not Prompt 05 `validate`."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from quantlab.app.certification import (
    certify_payload,
    checklist_payload,
    create_payload,
    diff_payload,
    domain_payload,
    inspect_payload,
    lineage_payload,
    list_payload,
    report_payload,
    reproduce_payload,
    retire_payload,
    risk_payload,
    run_payload,
    suspend_payload,
)


def add_validation_parser(sub: Any) -> None:
    parser = sub.add_parser(
        "validation",
        help="model-risk independent validation / pre-live certification (not live)",
    )
    cmd = parser.add_subparsers(dest="validation_cmd", required=True)
    cmd.add_parser("list", help="list certification candidates")
    inspect_p = cmd.add_parser("inspect", help="inspect a candidate")
    inspect_p.add_argument("item_id", nargs="?", default="last")
    create_p = cmd.add_parser("create", help="create a draft candidate")
    create_p.add_argument("item_id", nargs="?", default="seed-candidate")
    create_p.add_argument("--ledger", default="")
    for name in (
        "checklist",
        "run",
        "reproduce",
        "risk",
        "stability",
        "economics",
        "execution",
        "paper",
        "operations",
        "safety",
        "certify",
        "suspend",
        "retire",
        "report",
        "lineage",
    ):
        item = cmd.add_parser(name, help=f"validation {name}")
        item.add_argument("item_id", nargs="?", default="last")
        item.add_argument("--ledger", default="")
    diff_p = cmd.add_parser("diff", help="diff two candidates")
    diff_p.add_argument("item_id", nargs="?", default="last")
    diff_p.add_argument("other_id", nargs="?", default="last")


def add_research_certification_parsers(research_sub: Any) -> None:
    for name, help_text in (
        ("model-risk", "model-risk taxonomy"),
        ("validation", "independent validation checklist"),
        ("certification", "pre-live certification state machine"),
        ("reproducibility", "validation replay / hash compare"),
        ("readiness", "controlled-stage readiness"),
        ("governance", "roles, waivers, AI denial"),
    ):
        item = research_sub.add_parser(name, help=help_text)
        item.add_argument("item_id", nargs="?", default="last")
        item.add_argument("--ledger", default="")


def run_validation_command(args: Any) -> int:
    cmd = args.validation_cmd
    item = getattr(args, "item_id", "last")
    mapping: dict[str, Callable[[], Any]] = {
        "list": list_payload,
        "inspect": lambda: inspect_payload(item),
        "create": lambda: create_payload(
            candidate_id=item,
            ledger=getattr(args, "ledger", ""),
        ),
        "checklist": lambda: checklist_payload(item),
        "run": lambda: run_payload(candidate_id=item, ledger=getattr(args, "ledger", "")),
        "reproduce": lambda: reproduce_payload(item),
        "risk": lambda: risk_payload(item),
        "stability": lambda: domain_payload("regime_stability", item),
        "economics": lambda: domain_payload("oos_validation", item),
        "execution": lambda: domain_payload("execution_validation", item),
        "paper": lambda: domain_payload("paper_reconciliation", item),
        "operations": lambda: domain_payload("operational_readiness", item),
        "safety": lambda: domain_payload("safety", item),
        "certify": lambda: certify_payload(item),
        "suspend": lambda: suspend_payload(item),
        "retire": lambda: retire_payload(item),
        "report": lambda: report_payload(item),
        "lineage": lambda: lineage_payload(item),
        "diff": lambda: diff_payload(item, getattr(args, "other_id", "last")),
    }
    print(json.dumps(mapping[cmd](), indent=2, default=str))
    return 0


def run_research_certification_command(args: Any) -> int:
    cmd = args.research_cmd
    item = getattr(args, "item_id", "last")
    run_payload(candidate_id=item, ledger=getattr(args, "ledger", ""))
    if cmd == "model-risk":
        print(json.dumps(risk_payload(item), indent=2, default=str))
    elif cmd == "reproducibility":
        print(json.dumps(reproduce_payload(item), indent=2, default=str))
    elif cmd == "governance" or cmd == "readiness" or cmd == "certification":
        print(json.dumps(report_payload(item), indent=2, default=str))
    else:
        print(json.dumps(checklist_payload(item), indent=2, default=str))
    return 0
