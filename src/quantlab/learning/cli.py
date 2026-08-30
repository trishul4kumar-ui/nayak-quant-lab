"""quantlab model commands. Statistical models; not a live agent."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quantlab.core.config import get_settings
from quantlab.core.errors import ModelError
from quantlab.data.fabric.layout import resolve_fabric_root
from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.domain.models import Instrument
from quantlab.learning.registry import get_model, list_models


def add_model_parser(sub: Any) -> None:
    parser = sub.add_parser("model", help="statistical learning research")
    cmd = parser.add_subparsers(dest="model_cmd", required=True)
    cmd.add_parser("list", help="list seed statistical models")
    inspect_p = cmd.add_parser("inspect", help="print a model definition")
    inspect_p.add_argument("item_id")
    for name, help_text in (
        ("fit", "walk-forward fit experiment"),
        ("predict", "walk-forward scores summary"),
        ("evaluate", "OOS IC / RMSE"),
        ("stability", "coefficient stability flags"),
        ("importance", "linear or permutation importance"),
        ("residuals", "residual diagnostics"),
    ):
        item = cmd.add_parser(name, help=help_text)
        item.add_argument("item_id", nargs="?", default="ols_mom")
        _add_common(item)
    compare_p = cmd.add_parser("compare", help="baseline vs linear vs regularized vs tree")
    compare_p.add_argument("item_a", nargs="?", default="ols_mom")
    compare_p.add_argument("item_b", nargs="?", default="ridge_mom")
    _add_common(compare_p)
    select_p = cmd.add_parser("select", help="train-only selection experiment")
    select_p.add_argument("item_id", nargs="?", default="select_ols_mom")
    _add_common(select_p)


def _add_common(parser: Any) -> None:
    parser.add_argument("--ledger", default="")
    parser.add_argument("--n-days", type=int, default=80)
    parser.add_argument("--family-size", type=int, default=1)


def run_model_command(args: Any) -> int:
    if args.model_cmd == "list":
        rows = [
            {
                "model_id": item.model_id,
                "version": item.version,
                "algorithm": item.algorithm.value,
                "features": item.features,
                "identity": item.identity_hash(),
            }
            for item in list_models()
        ]
        print(json.dumps(rows, indent=2))
        return 0
    if args.model_cmd == "inspect":
        model = get_model(args.item_id)
        payload = model.model_dump(mode="json")
        payload["identity_hash"] = model.identity_hash()
        print(json.dumps(payload, indent=2))
        return 0
    if args.model_cmd == "compare":
        from quantlab.learning.experiment import run_model_comparison

        provider = MemoryBarProvider(n_days=getattr(args, "n_days", 80))
        bars = provider.all_bars()
        instruments = [Instrument(id=inst, name=inst.symbol) for inst in bars]
        comparison = run_model_comparison(
            bars=bars,
            instruments=instruments,
            model_ids=[args.item_a, args.item_b],
            ledger_path=_ledger_path(getattr(args, "ledger", "")),
            append=False,
        )
        print(json.dumps(comparison.model_dump(mode="json"), indent=2, default=str))
        return 0
    from quantlab.learning.experiment import run_named_model_experiment

    try:
        report, run, wf = run_named_model_experiment(
            args.item_id,
            ledger_path=_ledger_path(args.ledger),
            n_days=args.n_days,
            family_size=args.family_size,
            fabric_root=resolve_fabric_root(),
            append=True,
        )
    except ModelError as exc:
        print(json.dumps({"error": str(exc), "blocked": True}))
        return 1
    if args.model_cmd == "stability":
        print(json.dumps(report.stability.model_dump(mode="json"), indent=2))
        return 0
    if args.model_cmd == "importance":
        print(json.dumps(report.importance.model_dump(mode="json"), indent=2))
        return 0
    if args.model_cmd == "residuals":
        print(json.dumps(report.residuals.model_dump(mode="json"), indent=2))
        return 0
    if args.model_cmd == "predict":
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
                "model_id": report.model_id,
                "identity_hash": report.identity_hash,
                "algorithm": get_model(report.model_id).algorithm.value,
                "gate_outcome": report.gate.outcome.value,
                "data_kind": report.data_kind,
                "mean_ic": wf.mean_ic,
                "oos_rmse": wf.oos_rmse,
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
