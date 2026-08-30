"""quantlab ensemble commands. Combination research; not Prompt 07 portfolios."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quantlab.core.config import get_settings
from quantlab.core.errors import EnsembleError, InfeasibleEnsemble
from quantlab.data.fabric.layout import resolve_fabric_root
from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.domain.models import Instrument
from quantlab.ensemble.registry import get_ensemble, list_ensembles


def add_ensemble_parser(sub: Any) -> None:
    parser = sub.add_parser("ensemble", help="combination / meta-alpha research")
    cmd = parser.add_subparsers(dest="ensemble_cmd", required=True)
    cmd.add_parser("list", help="list seed combination ensembles")
    inspect_p = cmd.add_parser("inspect", help="print an ensemble definition")
    inspect_p.add_argument("item_id")
    build_p = cmd.add_parser("build", help="print frozen identity and components")
    build_p.add_argument("item_id", nargs="?", default="ew_mom_5_20")
    for name, help_text in (
        ("fit", "PIT combine experiment"),
        ("predict", "score coverage summary"),
        ("evaluate", "OOS IC vs equal-weight and best component"),
        ("weights", "weight path summary"),
        ("correlation", "pairwise component score correlation"),
        ("diversity", "redundancy diagnostics"),
        ("attribution", "leave-one-out ΔIC"),
        ("stability", "weight stability flags"),
        ("leave-one-out", "full vs each component removed"),
    ):
        item = cmd.add_parser(name, help=help_text)
        item.add_argument("item_id", nargs="?", default="ew_mom_5_20")
        _add_common(item)
    compare_p = cmd.add_parser("compare", help="equal vs static vs corr vs stack")
    compare_p.add_argument("item_a", nargs="?", default="ew_mom_5_20")
    compare_p.add_argument("item_b", nargs="?", default="ridge_stack_mom")
    _add_common(compare_p)
    select_p = cmd.add_parser("select", help="family comparison; records all candidates")
    select_p.add_argument("item_id", nargs="?", default="ew_mom_5_20")
    _add_common(select_p)


def _add_common(parser: Any) -> None:
    parser.add_argument("--ledger", default="")
    parser.add_argument("--n-days", type=int, default=80)
    parser.add_argument("--family-size", type=int, default=1)


def run_ensemble_command(args: Any) -> int:
    if args.ensemble_cmd == "list":
        rows = [
            {
                "ensemble_id": item.ensemble_id,
                "version": item.version,
                "weighting_policy": item.weighting_policy.value,
                "combination_method": item.combination_method.value,
                "components": item.component_ids(),
                "identity": item.identity_hash(),
            }
            for item in list_ensembles()
        ]
        print(json.dumps(rows, indent=2))
        return 0
    if args.ensemble_cmd in {"inspect", "build"}:
        model = get_ensemble(args.item_id)
        payload = model.model_dump(mode="json")
        payload["identity_hash"] = model.identity_hash()
        payload["note"] = (
            "Prompt 12 combination ensemble. Distinct from Prompt 07 alpha ensemble / portfolio."
        )
        print(json.dumps(payload, indent=2))
        return 0
    if args.ensemble_cmd == "compare":
        from quantlab.ensemble.experiment import run_ensemble_comparison

        provider = MemoryBarProvider(n_days=getattr(args, "n_days", 80))
        bars = provider.all_bars()
        instruments = [Instrument(id=inst, name=inst.symbol) for inst in bars]
        comparison = run_ensemble_comparison(
            bars=bars,
            instruments=instruments,
            ensemble_ids=[args.item_a, args.item_b],
            ledger_path=_ledger_path(getattr(args, "ledger", "")),
            append=False,
        )
        print(json.dumps(comparison.model_dump(mode="json"), indent=2, default=str))
        return 0
    if args.ensemble_cmd == "select":
        from quantlab.ensemble.experiment import run_ensemble_comparison

        provider = MemoryBarProvider(n_days=getattr(args, "n_days", 80))
        bars = provider.all_bars()
        instruments = [Instrument(id=inst, name=inst.symbol) for inst in bars]
        comparison = run_ensemble_comparison(
            bars=bars,
            instruments=instruments,
            ledger_path=_ledger_path(getattr(args, "ledger", "")),
            append=False,
        )
        print(json.dumps(comparison.model_dump(mode="json"), indent=2, default=str))
        return 0
    from quantlab.ensemble.experiment import run_named_ensemble_experiment

    try:
        report, run, wf = run_named_ensemble_experiment(
            args.item_id,
            ledger_path=_ledger_path(args.ledger),
            n_days=args.n_days,
            family_size=args.family_size,
            fabric_root=resolve_fabric_root(),
            append=True,
        )
    except (EnsembleError, InfeasibleEnsemble) as exc:
        print(json.dumps({"error": str(exc), "blocked": True}))
        return 1
    if args.ensemble_cmd == "weights":
        print(
            json.dumps(
                {
                    "experiment_id": run.id,
                    "n_steps": len(wf.weights_path),
                    "last": wf.weights_path[-1] if wf.weights_path else {},
                    "mean_turnover": wf.mean_weight_turnover,
                },
                indent=2,
                default=str,
            )
        )
        return 0
    if args.ensemble_cmd == "correlation":
        print(
            json.dumps(
                [p.model_dump(mode="json") for p in report.diversity.pairs],
                indent=2,
            )
        )
        return 0
    if args.ensemble_cmd == "diversity":
        print(json.dumps(report.diversity.model_dump(mode="json"), indent=2))
        return 0
    if args.ensemble_cmd == "attribution":
        print(json.dumps(report.attribution.model_dump(mode="json"), indent=2))
        return 0
    if args.ensemble_cmd == "stability":
        print(json.dumps(report.stability.model_dump(mode="json"), indent=2))
        return 0
    if args.ensemble_cmd == "leave-one-out":
        print(json.dumps(report.leave_one_out.model_dump(mode="json"), indent=2))
        return 0
    if args.ensemble_cmd == "predict":
        print(
            json.dumps(
                {
                    "experiment_id": run.id,
                    "n_predictions": wf.n_predictions,
                    "coverage": wf.coverage,
                    "note": wf.note,
                },
                indent=2,
            )
        )
        return 0
    print(
        json.dumps(
            {
                "experiment_id": run.id,
                "ensemble_id": report.ensemble_id,
                "identity_hash": report.identity_hash,
                "weighting_policy": report.weighting_policy,
                "gate_outcome": report.gate.outcome.value,
                "data_kind": report.data_kind,
                "mean_ic": wf.mean_ic,
                "equal_weight_ic": wf.equal_weight_ic,
                "best_component_id": wf.best_component_id,
                "best_component_ic": wf.best_component_ic,
                "n_scored": wf.n_scored,
                "integrity": report.integrity,
                "note": report.note,
            },
            indent=2,
            default=str,
        )
    )
    return 0


def _ledger_path(raw: str) -> Path:
    if raw:
        return Path(raw)
    return Path(get_settings().experiment_ledger_path)
