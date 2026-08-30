"""quantlab adaptive commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quantlab.adaptive.decay import estimate_half_life
from quantlab.adaptive.engine import compute_alpha_panel
from quantlab.adaptive.registry import get_adaptive_model, list_adaptive_models
from quantlab.core.config import get_settings
from quantlab.core.errors import AdaptiveError
from quantlab.data.fabric.layout import resolve_fabric_root
from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.features.engine import session_calendar
from quantlab.labels.definition import forward_return
from quantlab.labels.engine import compute_label_panel
from quantlab.research.cross_section import spearman_ic


def add_adaptive_parser(sub: Any) -> None:
    parser = sub.add_parser("adaptive", help="adaptive alpha and online-learning research")
    cmd = parser.add_subparsers(dest="adaptive_cmd", required=True)
    cmd.add_parser("list", help="list seed adaptive models")
    inspect_p = cmd.add_parser("inspect", help="print an adaptive-model definition")
    inspect_p.add_argument("item_id")
    for name, help_text in (
        ("run", "prequential experiment"),
        ("state", "final learner state after a run"),
        ("drift", "IC CUSUM drift report"),
        ("stability", "adaptation stability flags"),
        ("prequential", "prequential IC summary"),
    ):
        item = cmd.add_parser(name, help=help_text)
        item.add_argument("item_id", nargs="?", default="static_mom20")
        _add_common(item)
    decay_p = cmd.add_parser("decay", help="half-life of an alpha's realized IC")
    decay_p.add_argument("alpha_id", nargs="?", default="rank_momentum_20")
    compare_p = cmd.add_parser("compare", help="static vs rolling vs ewma vs ensemble")
    compare_p.add_argument("item_a", nargs="?", default="static_mom20")
    compare_p.add_argument("item_b", nargs="?", default="ensemble_ic_mom")
    _add_common(compare_p)


def _add_common(parser: Any) -> None:
    parser.add_argument("--ledger", default="")
    parser.add_argument("--n-days", type=int, default=80)
    parser.add_argument("--family-size", type=int, default=1)


def run_adaptive_command(args: Any) -> int:
    if args.adaptive_cmd == "list":
        rows = [
            {
                "adaptive_model_id": item.adaptive_model_id,
                "version": item.version,
                "policy": item.policy.value,
                "learner": item.learner.value,
                "alphas": item.alpha_ids,
                "identity": item.identity_hash(),
            }
            for item in list_adaptive_models()
        ]
        print(json.dumps(rows, indent=2))
        return 0
    if args.adaptive_cmd == "inspect":
        model = get_adaptive_model(args.item_id)
        payload = model.model_dump(mode="json")
        payload["identity_hash"] = model.identity_hash()
        print(json.dumps(payload, indent=2))
        return 0
    if args.adaptive_cmd == "decay":
        provider = MemoryBarProvider(n_days=80)
        bars = provider.all_bars()
        dates = session_calendar(bars)
        panel = compute_alpha_panel(args.alpha_id, bars, dates)
        labels = compute_label_panel(forward_return(1), bars, dates)
        ics = [
            ic
            for as_of in dates
            if (ic := spearman_ic(panel.get(as_of, {}), labels.get(as_of, {}))) is not None
        ]
        print(json.dumps(estimate_half_life(ics).model_dump(mode="json"), indent=2))
        return 0
    if args.adaptive_cmd == "compare":
        from quantlab.adaptive.experiment import run_adaptive_comparison
        from quantlab.domain.models import Instrument

        provider = MemoryBarProvider(n_days=getattr(args, "n_days", 80))
        bars = provider.all_bars()
        instruments = [Instrument(id=inst, name=inst.symbol) for inst in bars]
        comparison = run_adaptive_comparison(
            bars=bars,
            instruments=instruments,
            model_ids=[args.item_a, args.item_b],
            ledger_path=_ledger_path(getattr(args, "ledger", "")),
            append=False,
        )
        print(json.dumps(comparison.model_dump(mode="json"), indent=2, default=str))
        return 0
    from quantlab.adaptive.experiment import run_named_adaptive_experiment

    try:
        report, run, preq = run_named_adaptive_experiment(
            args.item_id,
            ledger_path=_ledger_path(args.ledger),
            n_days=args.n_days,
            family_size=args.family_size,
            fabric_root=resolve_fabric_root(),
            append=True,
        )
    except AdaptiveError as exc:
        print(json.dumps({"error": str(exc), "blocked": True}))
        return 1
    if args.adaptive_cmd == "state":
        state_payload = (
            None if preq.final_state is None else preq.final_state.model_dump(mode="json")
        )
        print(json.dumps({"experiment_id": run.id, "state": state_payload}, indent=2, default=str))
        return 0
    if args.adaptive_cmd == "drift":
        from quantlab.adaptive.drift import classify_drift

        ics = [p.ic for p in preq.points if p.ic is not None]
        print(json.dumps(classify_drift(ics).model_dump(mode="json"), indent=2))
        return 0
    if args.adaptive_cmd == "stability":
        print(json.dumps(report.stability.model_dump(mode="json"), indent=2))
        return 0
    if args.adaptive_cmd == "prequential":
        print(
            json.dumps(
                {
                    "experiment_id": run.id,
                    "mean_ic": preq.mean_ic,
                    "n_scored": preq.n_scored,
                    "coverage": preq.coverage,
                    "hit_rate": preq.hit_rate,
                    "gate_outcome": report.gate.outcome.value,
                    "note": preq.note,
                },
                indent=2,
            )
        )
        return 0
    print(
        json.dumps(
            {
                "experiment_id": run.id,
                "adaptive_model_id": report.adaptive_model_id,
                "identity_hash": report.identity_hash,
                "gate_outcome": report.gate.outcome.value,
                "data_kind": report.data_kind,
                "mean_ic": preq.mean_ic,
                "n_scored": preq.n_scored,
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
