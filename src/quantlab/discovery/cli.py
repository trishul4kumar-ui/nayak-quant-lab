"""quantlab discovery commands. Research search; not a second gate or OMS."""

from __future__ import annotations

import json
from typing import Any

from quantlab.app.discovery import (
    archive_payload,
    compare_expressions,
    complexity_payload,
    evaluate_expression_text,
    family_rows,
    inspect_family,
    last_discovery_payload,
    lineage_payload,
    mutate_seed,
    pareto_payload,
    redundancy_payload,
    replicate_named_search,
    run_named_search,
    simplify_seed,
)


def add_discovery_parser(sub: Any) -> None:
    parser = sub.add_parser("discovery", help="symbolic / genetic alpha discovery")
    cmd = parser.add_subparsers(dest="discovery_cmd", required=True)
    cmd.add_parser("list", help="list discovery families")
    inspect_p = cmd.add_parser("inspect", help="inspect a discovery family")
    inspect_p.add_argument("family_id", nargs="?", default="GP-MOM-VOL-001")
    cmd.add_parser("generate", help="print seed expressions")
    search_p = cmd.add_parser("search", help="run a frozen genetic search")
    search_p.add_argument("family_id", nargs="?", default="GP-MOM-VOL-001")
    _ledger_days(search_p)
    evolve_p = cmd.add_parser("evolve", help="alias of search")
    evolve_p.add_argument("family_id", nargs="?", default="GP-MOM-VOL-001")
    _ledger_days(evolve_p)
    eval_p = cmd.add_parser("evaluate", help="evaluate a seed expression text")
    eval_p.add_argument("expression", nargs="?", default="rank(momentum_20)")
    _ledger_days(eval_p)
    cmd.add_parser("mutate", help="mutate a seed expression")
    cmd.add_parser("crossover", help="crossover two seed expressions")
    cmd.add_parser("simplify", help="simplify a seed expression")
    cmd.add_parser("archive", help="list archived candidates from last run")
    lin = cmd.add_parser("lineage", help="print discovery lineage")
    lin.add_argument("family_id", nargs="?", default="GP-MOM-VOL-001")
    _ledger_days(lin)
    fal = cmd.add_parser("falsify", help="run search and report falsification")
    fal.add_argument("family_id", nargs="?", default="GP-MOM-VOL-001")
    _ledger_days(fal)
    val = cmd.add_parser("validate", help="train/val/holdout IC for elite")
    val.add_argument("family_id", nargs="?", default="GP-MOM-VOL-001")
    _ledger_days(val)
    rep = cmd.add_parser("replicate", help="replay a frozen discovery search")
    rep.add_argument("family_id", nargs="?", default="GP-MOM-VOL-001")
    _ledger_days(rep)
    report_p = cmd.add_parser("report", help="last discovery ledger row")
    report_p.add_argument("--ledger", default="")
    cmd.add_parser("compare", help="compare two seed expression hashes")
    cmd.add_parser("pareto", help="pareto view of last search")
    cmd.add_parser("redundancy", help="feature overlap of seeds")
    cmd.add_parser("complexity", help="complexity of seed expressions")
    cmd.add_parser("sensitivity", help="note: cost sensitivity stays on Prompt 14")


def add_research_discovery_parsers(research_sub: Any) -> None:
    for name, help_text in (
        ("symbolic", "symbolic discovery alias"),
        ("genetic", "genetic discovery alias"),
        ("alpha-discovery", "run GP-MOM-VOL-001"),
        ("novelty", "novelty classes from last search"),
        ("expression", "inspect seed expressions"),
        ("discovery-family", "inspect GP-MOM-VOL-001"),
    ):
        item = research_sub.add_parser(name, help=help_text)
        item.add_argument("family_id", nargs="?", default="GP-MOM-VOL-001")
        _ledger_days(item)


def _ledger_days(parser: Any) -> None:
    parser.add_argument("--ledger", default="")
    parser.add_argument("--n-days", type=int, default=80)


def run_discovery_command(args: Any) -> int:
    cmd = args.discovery_cmd
    if cmd == "list":
        print(json.dumps(family_rows(), indent=2))
        return 0
    if cmd == "inspect":
        print(json.dumps(inspect_family(args.family_id), indent=2))
        return 0
    if cmd == "generate":
        print(json.dumps(inspect_family("GP-MOM-VOL-001")["seeds"], indent=2))
        return 0
    if cmd in {"search", "evolve", "falsify", "validate"}:
        report, summary = run_named_search(
            getattr(args, "family_id", "GP-MOM-VOL-001"),
            ledger=getattr(args, "ledger", ""),
            n_days=getattr(args, "n_days", 80),
        )
        payload = dict(summary)
        payload["discovery_status"] = report.discovery_status
        payload["gate"] = report.gate.outcome.value if report.gate else ""
        print(json.dumps(payload, indent=2, default=str))
        return 0
    if cmd == "evaluate":
        print(json.dumps(evaluate_expression_text(args.expression), indent=2))
        return 0
    if cmd == "mutate":
        print(json.dumps(mutate_seed(), indent=2))
        return 0
    if cmd == "crossover":
        print(json.dumps(mutate_seed(do_crossover=True), indent=2))
        return 0
    if cmd == "simplify":
        print(json.dumps(simplify_seed(), indent=2))
        return 0
    if cmd == "archive":
        print(json.dumps(archive_payload(getattr(args, "ledger", "")), indent=2))
        return 0
    if cmd == "lineage":
        print(json.dumps(lineage_payload(args.family_id, getattr(args, "ledger", "")), indent=2))
        return 0
    if cmd == "replicate":
        print(
            json.dumps(
                replicate_named_search(args.family_id, ledger=args.ledger, n_days=args.n_days),
                indent=2,
            )
        )
        return 0
    if cmd == "report":
        print(json.dumps(last_discovery_payload(args.ledger), indent=2, default=str))
        return 0
    if cmd == "compare":
        print(json.dumps(compare_expressions(), indent=2))
        return 0
    if cmd == "pareto":
        print(json.dumps(pareto_payload(getattr(args, "ledger", "")), indent=2))
        return 0
    if cmd == "redundancy":
        print(json.dumps(redundancy_payload(), indent=2))
        return 0
    if cmd == "complexity":
        print(json.dumps(complexity_payload(), indent=2))
        return 0
    print(
        json.dumps(
            {
                "note": "Cost/parameter sensitivity remains Prompt 14 research sensitivity.",
                "live_trading": False,
            },
            indent=2,
        )
    )
    return 0


def run_research_discovery_command(args: Any) -> int:
    cmd = args.research_cmd
    if cmd in {"symbolic", "genetic", "alpha-discovery"}:
        report, summary = run_named_search(
            getattr(args, "family_id", "GP-MOM-VOL-001"),
            ledger=getattr(args, "ledger", ""),
            n_days=getattr(args, "n_days", 80),
        )
        payload = dict(summary)
        payload["alias"] = cmd
        payload["discovery_status"] = report.discovery_status
        print(json.dumps(payload, indent=2, default=str))
        return 0
    if cmd == "novelty":
        print(json.dumps(pareto_payload(getattr(args, "ledger", "")), indent=2))
        return 0
    if cmd == "expression":
        print(json.dumps(inspect_family("GP-MOM-VOL-001")["seeds"], indent=2))
        return 0
    print(json.dumps(inspect_family(getattr(args, "family_id", "GP-MOM-VOL-001")), indent=2))
    return 0
