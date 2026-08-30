"""quantlab knowledge commands. Memory layer; not a second gate."""

from __future__ import annotations

import json
from typing import Any

from quantlab.app.knowledge import (
    contradiction_payload,
    dead_end_payload,
    diff_payload,
    evidence_payload,
    export_payload,
    failures_payload,
    family_payload,
    graph_payload,
    inspect_payload,
    lineage_payload,
    list_payload,
    replication_payload,
    report_payload,
    search_payload,
    similar_payload,
    snapshot_payload,
    status_payload,
)


def add_knowledge_parser(sub: Any) -> None:
    parser = sub.add_parser("knowledge", help="research memory / knowledge graph")
    cmd = parser.add_subparsers(dest="knowledge_cmd", required=True)
    cmd.add_parser("list", help="list knowledge nodes")
    inspect_p = cmd.add_parser("inspect", help="inspect a node or hypothesis")
    inspect_p.add_argument("item_id", nargs="?", default="H-MOM-001")
    search_p = cmd.add_parser("search", help="search nodes by substring")
    search_p.add_argument("query", nargs="?", default="momentum")
    graph_p = cmd.add_parser("graph", help="print incident edges")
    graph_p.add_argument("item_id", nargs="?", default="hypothesis:H-MOM-001")
    lin = cmd.add_parser("lineage", help="walk knowledge lineage")
    lin.add_argument("item_id", nargs="?", default="hypothesis:H-MOM-001")
    ev = cmd.add_parser("evidence", help="list evidence for a hypothesis")
    ev.add_argument("item_id", nargs="?", default="H-MOM-001")
    st = cmd.add_parser("status", help="hypothesis knowledge status")
    st.add_argument("item_id", nargs="?", default="H-MOM-001")
    sim = cmd.add_parser("similar", help="compare two seed expressions")
    sim.add_argument("item_id", nargs="?", default="rank(momentum_20)")
    fam = cmd.add_parser("family", help="list an alpha family")
    fam.add_argument("item_id", nargs="?", default="MOMENTUM")
    fail = cmd.add_parser("failures", help="list dead-ends / failures")
    fail.add_argument("item_id", nargs="?", default="")
    rep = cmd.add_parser("replications", help="list replications")
    rep.add_argument("item_id", nargs="?", default="H-MOM-001")
    cmd.add_parser("contradictions", help="list unresolved contradictions")
    cmd.add_parser("snapshot", help="freeze a knowledge snapshot")
    diff = cmd.add_parser("diff", help="diff two snapshots")
    diff.add_argument("snapshot_a", nargs="?", default="KS-SEED-001")
    diff.add_argument("snapshot_b", nargs="?", default="KS-SEED-001")
    report_p = cmd.add_parser("report", help="scientific memory report")
    report_p.add_argument("hypothesis_id", nargs="?", default="H-MOM-001")
    cmd.add_parser("export", help="export the graph JSON")


def add_research_knowledge_parsers(research_sub: Any) -> None:
    for name, help_text in (
        ("knowledge", "research memory overview"),
        ("genealogy", "knowledge lineage walk"),
        ("dead-ends", "failed research retained in memory"),
        ("replication", "knowledge replications (not Prompt 14 replicate)"),
        ("contradictions", "unresolved claim conflicts"),
        ("similarity", "expression similarity class"),
        ("evidence", "evidence records for a hypothesis"),
        ("alpha-family", "alpha family membership"),
    ):
        item = research_sub.add_parser(name, help=help_text)
        item.add_argument("item_id", nargs="?", default="H-MOM-001")


def run_knowledge_command(args: Any) -> int:
    cmd = args.knowledge_cmd
    mapping = {
        "list": lambda: list_payload(),
        "inspect": lambda: inspect_payload(args.item_id),
        "search": lambda: search_payload(args.query),
        "graph": lambda: graph_payload(args.item_id),
        "lineage": lambda: lineage_payload(args.item_id),
        "evidence": lambda: evidence_payload(args.item_id),
        "status": lambda: status_payload(args.item_id),
        "similar": lambda: similar_payload(args.item_id),
        "family": lambda: family_payload(args.item_id),
        "failures": lambda: failures_payload(),
        "replications": lambda: replication_payload(args.item_id),
        "contradictions": contradiction_payload,
        "snapshot": snapshot_payload,
        "diff": lambda: diff_payload(args.snapshot_a, args.snapshot_b),
        "report": lambda: report_payload(args.hypothesis_id),
        "export": export_payload,
    }
    action = mapping[cmd]
    print(json.dumps(action(), indent=2, default=str))
    return 0


def run_research_knowledge_command(args: Any) -> int:
    cmd = args.research_cmd
    item = getattr(args, "item_id", "H-MOM-001")
    if cmd == "knowledge":
        print(json.dumps(list_payload(), indent=2, default=str))
    elif cmd == "genealogy":
        print(json.dumps(lineage_payload(f"hypothesis:{item}"), indent=2, default=str))
    elif cmd == "dead-ends":
        print(json.dumps(dead_end_payload(), indent=2, default=str))
    elif cmd == "replication":
        print(json.dumps(replication_payload(item), indent=2, default=str))
    elif cmd == "contradictions":
        print(json.dumps(contradiction_payload(), indent=2, default=str))
    elif cmd == "similarity":
        print(json.dumps(similar_payload(item), indent=2, default=str))
    elif cmd == "evidence":
        print(json.dumps(evidence_payload(item), indent=2, default=str))
    else:
        print(json.dumps(family_payload("MOMENTUM"), indent=2, default=str))
    return 0
