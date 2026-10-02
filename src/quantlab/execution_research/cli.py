"""quantlab execution commands. Research simulation; not OMS live submit."""
# ruff: noqa: E501

from __future__ import annotations

import json
from typing import Any

from quantlab.app.execution import (
    execution_report,
    inspect_execution_model,
    list_execution_model_rows,
    simulate_execution_experiment,
)
from quantlab.core.errors import ExecutionResearchError


def add_execution_parser(sub: Any) -> None:
    parser = sub.add_parser("execution", help="microstructure and execution-research simulation")
    cmd = parser.add_subparsers(dest="execution_cmd", required=True)
    cmd.add_parser("list", help="list seed execution models")
    inspect_p = cmd.add_parser("inspect", help="print an execution-model definition")
    inspect_p.add_argument("item_id")
    simulate_p = cmd.add_parser("simulate", help="simulate fills on the synthetic momentum path")
    simulate_p.add_argument("item_id", nargs="?", default="exec_base")
    _add_common(simulate_p)
    report_p = cmd.add_parser("report", help="print a saved execution experiment")
    report_p.add_argument("experiment")
    report_p.add_argument("--ledger", default="")
    # Restricted gateway commands are intentionally non-interactive at the CLI.
    # Existing research commands remain separate from this safety boundary.
    cmd.add_parser("preview", help="show the disabled restricted-execution boundary")
    cmd.add_parser("validate", help="validate current restricted-execution readiness")
    cmd.add_parser("status", help="show restricted-execution attempts")
    cmd.add_parser("submit", help="blocked: interactive human confirmation is required")
    cmd.add_parser("cancel", help="blocked: a separate interactive confirmation is required")
    reconcile_p = cmd.add_parser("reconcile", help="record a read-only gateway reconciliation")
    reconcile_p.add_argument("envelope_hash", nargs="?", default="")
    reconcile_p.add_argument("--observed", action="store_true")
    for name, help_text in (
        ("spread", "spread cost summary"),
        ("slippage", "slippage cost summary"),
        ("impact", "impact cost summary"),
        ("liquidity", "fill participation summary"),
        ("latency", "arrival delay summary"),
        ("fills", "simulated fill table"),
        ("costs", "cost attribution"),
        ("attribution", "gross vs net execution drag"),
        ("sensitivity", "spread/slip/participation grid"),
        ("capacity", "notional capacity scenarios"),
        ("stress", "stressed microstructure overlay"),
    ):
        item = cmd.add_parser(name, help=help_text)
        item.add_argument("item_id", nargs="?", default="exec_base")
        _add_common(item)


def _add_common(parser: Any) -> None:
    parser.add_argument("--ledger", default="")
    parser.add_argument("--n-days", type=int, default=80)
    parser.add_argument("--family-size", type=int, default=1)
    parser.add_argument("--capital", type=float, default=1_000_000.0)
    parser.add_argument("--scenario", default="")


def run_execution_command(args: Any) -> int:
    if args.execution_cmd in {"preview", "validate", "status", "submit", "cancel", "reconcile"}:
        return _run_restricted_gateway_command(args)
    if args.execution_cmd == "list":
        print(json.dumps(list_execution_model_rows(), indent=2))
        return 0
    if args.execution_cmd == "inspect":
        print(json.dumps(inspect_execution_model(args.item_id), indent=2, default=str))
        return 0
    if args.execution_cmd == "report":
        payload = execution_report(args.experiment, ledger=getattr(args, "ledger", ""))
        if payload is None:
            print(json.dumps({"error": "experiment not found"}))
            return 1
        print(json.dumps(payload, indent=2, default=str))
        return 0
    try:
        report, summary = simulate_execution_experiment(
            args.item_id,
            ledger=args.ledger,
            n_days=args.n_days,
            family_size=args.family_size,
            capital=args.capital,
            scenario_id=args.scenario or None,
            append=True,
        )
    except (ExecutionResearchError, KeyError) as exc:
        print(json.dumps({"error": str(exc), "blocked": True}))
        return 1
    cmd = args.execution_cmd
    if cmd == "spread":
        print(json.dumps({"spread_cost": report.simulation.spread_cost, **summary}, indent=2))
        return 0
    if cmd == "slippage":
        print(json.dumps({"slippage_cost": report.simulation.slippage_cost, **summary}, indent=2))
        return 0
    if cmd == "impact":
        print(
            json.dumps(
                {
                    "impact_cost": report.simulation.impact_cost,
                    "status": "uncalibrated",
                    **summary,
                },
                indent=2,
            )
        )
        return 0
    if cmd == "liquidity":
        print(
            json.dumps(
                {
                    "mean_participation": report.simulation.mean_participation,
                    "mean_fill_ratio": report.simulation.mean_fill_ratio,
                    "capacity_status": "not_tested",
                    **summary,
                },
                indent=2,
            )
        )
        return 0
    if cmd == "latency":
        fills = report.simulation.fills
        print(
            json.dumps(
                {
                    "n_fills": len(fills),
                    "sample_fill_timestamps": [str(f.timestamp) for f in fills[:8]],
                    "note": (
                        "no fill before market arrival; latency does not use future "
                        "prices to set delay"
                    ),
                    **summary,
                },
                indent=2,
                default=str,
            )
        )
        return 0
    if cmd == "fills":
        print(
            json.dumps(
                [f.model_dump(mode="json") for f in report.simulation.fills[:50]],
                indent=2,
                default=str,
            )
        )
        return 0
    if cmd == "costs":
        print(json.dumps(report.attribution.model_dump(mode="json"), indent=2))
        return 0
    if cmd == "attribution":
        print(json.dumps(report.alpha_attribution.model_dump(mode="json"), indent=2))
        return 0
    if cmd == "sensitivity":
        print(json.dumps(report.sensitivity.model_dump(mode="json"), indent=2))
        return 0
    if cmd == "capacity":
        print(json.dumps(report.capacity.model_dump(mode="json"), indent=2))
        return 0
    if cmd == "stress":
        print(
            json.dumps(
                {
                    "fragility": report.fragility_score,
                    "flags": report.fragility_flags,
                    **summary,
                },
                indent=2,
            )
        )
        return 0
    print(json.dumps(summary, indent=2, default=str))
    return 0


def _run_restricted_gateway_command(args: Any) -> int:
    """Keep shell invocation observational; it cannot supply a human confirmation."""
    from quantlab.restricted_execution.repository import list_submissions
    from quantlab.restricted_execution.service import RestrictedExecutionGateway

    cmd = args.execution_cmd
    if cmd == "status":
        print(
            json.dumps(
                {
                    "gateway": "disabled",
                    "production_write_adapter": "not configured",
                    "submissions": [item.model_dump(mode="json") for item in list_submissions()],
                },
                indent=2,
                default=str,
            )
        )
        return 0
    if cmd in {"submit", "cancel"}:
        print(
            json.dumps(
                {
                    "blocked": True,
                    "reason": "non-interactive CLI cannot perform human confirmation or broker submission",
                    "live_trading": False,
                },
                indent=2,
            )
        )
        return 1
    if cmd == "reconcile":
        if not args.envelope_hash:
            print(json.dumps({"blocked": True, "reason": "envelope_hash is required"}, indent=2))
            return 1
        try:
            result = RestrictedExecutionGateway().reconcile(
                args.envelope_hash, observed=args.observed
            )
        except KeyError:
            print(json.dumps({"blocked": True, "reason": "unknown envelope hash"}, indent=2))
            return 1
        print(json.dumps(result.model_dump(mode="json"), indent=2, default=str))
        return 0
    print(
        json.dumps(
            {
                "gateway": "restricted and disabled",
                "live_trading": False,
                "broker_write_enabled": False,
                "reason": "only an already-approved immutable envelope may be assessed in an interactive human workflow",
            },
            indent=2,
        )
    )
    return 0
