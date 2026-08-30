"""quantlab hypothesis / experiment commands. Control plane; not a second research gate."""

from __future__ import annotations

import json
from typing import Any

from quantlab.app.orchestration import (
    cancel_experiment,
    compare_hypotheses,
    create_hypothesis,
    experiment_rows,
    family_payload,
    hypothesis_rows,
    inspect_experiment,
    inspect_hypothesis,
    lineage_payload,
    orchestration_report,
    plan_named_experiment,
    replicate_named,
    research_status_payload,
    run_named_experiment,
)


def add_hypothesis_parser(sub: Any) -> None:
    parser = sub.add_parser("hypothesis", help="research hypotheses (control plane)")
    cmd = parser.add_subparsers(dest="hypothesis_cmd", required=True)
    cmd.add_parser("list", help="list registered hypotheses")
    inspect_p = cmd.add_parser("inspect", help="print a hypothesis")
    inspect_p.add_argument("item_id")
    create_p = cmd.add_parser("create", help="register a hypothesis")
    create_p.add_argument("item_id")
    create_p.add_argument("--title", default="Untitled hypothesis")
    create_p.add_argument("--description", default="")
    compare_p = cmd.add_parser("compare", help="compare two hypothesis identities")
    compare_p.add_argument("item_a")
    compare_p.add_argument("item_b")


def add_experiment_parser(sub: Any) -> None:
    parser = sub.add_parser("experiment", help="research experiments (control plane)")
    cmd = parser.add_subparsers(dest="experiment_cmd", required=True)
    cmd.add_parser("list", help="list frozen experiment specs")
    inspect_p = cmd.add_parser("inspect", help="print an experiment spec")
    inspect_p.add_argument("item_id")
    create_p = cmd.add_parser("create", help="inspect seed experiment (specs are versioned)")
    create_p.add_argument("item_id", nargs="?", default="EXP-MOM-001")
    plan_p = cmd.add_parser("plan", help="freeze a research plan")
    plan_p.add_argument("item_id")
    run_p = cmd.add_parser("run", help="execute a frozen experiment via existing engines")
    run_p.add_argument("item_id")
    run_p.add_argument("--ledger", default="")
    run_p.add_argument("--n-days", type=int, default=80)
    cancel_p = cmd.add_parser("cancel", help="refuse ledger rewrite; explain append-only cancel")
    cancel_p.add_argument("item_id")
    report_p = cmd.add_parser("report", help="print a ledger orchestration row")
    report_p.add_argument("item_id")
    report_p.add_argument("--ledger", default="")


def run_hypothesis_command(args: Any) -> int:
    if args.hypothesis_cmd == "list":
        print(json.dumps(hypothesis_rows(), indent=2))
        return 0
    if args.hypothesis_cmd == "inspect":
        print(json.dumps(inspect_hypothesis(args.item_id), indent=2, default=str))
        return 0
    if args.hypothesis_cmd == "create":
        print(
            json.dumps(
                create_hypothesis(args.item_id, args.title, args.description),
                indent=2,
                default=str,
            )
        )
        return 0
    print(json.dumps(compare_hypotheses(args.item_a, args.item_b), indent=2))
    return 0


def run_experiment_command(args: Any) -> int:
    if args.experiment_cmd == "list":
        print(json.dumps(experiment_rows(), indent=2))
        return 0
    if args.experiment_cmd == "inspect":
        print(json.dumps(inspect_experiment(args.item_id), indent=2, default=str))
        return 0
    if args.experiment_cmd == "create":
        print(json.dumps(inspect_experiment(args.item_id), indent=2, default=str))
        return 0
    if args.experiment_cmd == "plan":
        print(json.dumps(plan_named_experiment(args.item_id), indent=2))
        return 0
    if args.experiment_cmd == "run":
        report, summary = run_named_experiment(
            args.item_id,
            ledger=getattr(args, "ledger", ""),
            n_days=getattr(args, "n_days", 80),
        )
        payload = dict(summary)
        payload["not_tested"] = report.not_tested[:12]
        print(json.dumps(payload, indent=2, default=str))
        return 0
    if args.experiment_cmd == "cancel":
        print(json.dumps(cancel_experiment(args.item_id), indent=2))
        return 0
    payload = orchestration_report(args.item_id, ledger=getattr(args, "ledger", ""))
    print(json.dumps(payload, indent=2, default=str))
    return 0 if "error" not in payload else 1


def add_research_orchestration_parsers(research_sub: Any) -> None:
    discover = research_sub.add_parser("discover", help="run a discovery family")
    discover.add_argument("hypothesis_id", nargs="?", default="H-MOM-001")
    discover.add_argument("--experiment", default="EXP-MOM-001")
    _ledger_days(discover)
    replicate = research_sub.add_parser("replicate", help="replicate a frozen experiment")
    replicate.add_argument("experiment_id", nargs="?", default="EXP-MOM-001")
    _ledger_days(replicate)
    for name, help_text in (
        ("falsify", "sign-reversal / cost-stress falsification"),
        ("ablation", "lookback ablation of a recorded family"),
        ("sensitivity", "cost sensitivity of a recorded family"),
        ("grid", "expand and run the family grid"),
        ("lineage", "print hypothesis/family/candidate graph"),
        ("degrees-of-freedom", "researcher degrees of freedom"),
        ("pareto", "non-dominated family view"),
    ):
        item = research_sub.add_parser(name, help=help_text)
        item.add_argument("item_id", nargs="?", default="EXP-MOM-001")
        _ledger_days(item)
    family = research_sub.add_parser("family", help="inspect a research family")
    family.add_argument("family_id", nargs="?", default="MOM-FAMILY-001")
    mt = research_sub.add_parser("multiple-testing", help="family multiple-testing wrapper")
    mt.add_argument("family_id", nargs="?", default="MOM-FAMILY-001")
    research_sub.add_parser("status", help="research control-plane status")


def _ledger_days(parser: Any) -> None:
    parser.add_argument("--ledger", default="")
    parser.add_argument("--n-days", type=int, default=80)


def run_research_orchestration_command(args: Any) -> int:
    cmd = args.research_cmd
    if cmd == "status":
        print(json.dumps(research_status_payload(), indent=2))
        return 0
    if cmd == "family":
        print(json.dumps(family_payload(args.family_id), indent=2))
        return 0
    if cmd == "multiple-testing":
        from quantlab.app.orchestration import family_multiple_testing

        print(json.dumps(family_multiple_testing(args.family_id), indent=2))
        return 0
    if cmd == "lineage":
        print(json.dumps(lineage_payload(args.item_id), indent=2))
        return 0
    if cmd == "replicate":
        print(
            json.dumps(
                replicate_named(args.experiment_id, ledger=args.ledger, n_days=args.n_days),
                indent=2,
            )
        )
        return 0
    if cmd in {"discover", "grid"}:
        experiment_id = getattr(args, "experiment", "EXP-MOM-001")
        report, summary = run_named_experiment(
            experiment_id, ledger=args.ledger, n_days=args.n_days
        )
        payload = dict(summary)
        payload["hypothesis_requested"] = getattr(args, "hypothesis_id", "")
        payload["ablation"] = report.ablation.model_dump(mode="json")
        print(json.dumps(payload, indent=2, default=str))
        return 0
    report, summary = run_named_experiment(
        getattr(args, "item_id", "EXP-MOM-001"),
        ledger=getattr(args, "ledger", ""),
        n_days=getattr(args, "n_days", 80),
    )
    extra: dict[str, Any] = dict(summary)
    if cmd == "falsify":
        extra["falsification"] = report.falsification.model_dump(mode="json")
    elif cmd == "ablation":
        extra["ablation"] = report.ablation.model_dump(mode="json")
    elif cmd == "sensitivity":
        extra["sensitivity"] = report.sensitivity.model_dump(mode="json")
    elif cmd == "degrees-of-freedom":
        extra["degrees_of_freedom"] = report.degrees_of_freedom.model_dump(mode="json")
    elif cmd == "pareto":
        extra["pareto"] = report.pareto.model_dump(mode="json")
    print(json.dumps(extra, indent=2, default=str))
    return 0
