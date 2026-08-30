"""quantlab state / regime commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quantlab.core.config import get_settings
from quantlab.core.errors import RegimeError
from quantlab.data.fabric.layout import resolve_fabric_root
from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.regimes.definition import DetectorKind
from quantlab.regimes.duration import durations
from quantlab.regimes.engine import classify, compute_state_panel, detect_changes
from quantlab.regimes.registry import (
    get_regime_model,
    get_state_variable,
    list_regime_models,
    list_state_variables,
)
from quantlab.regimes.transitions import transition_matrix


def add_state_parser(sub: Any) -> None:
    parser = sub.add_parser("state", help="cross-sectional market-state snapshots")
    cmd = parser.add_subparsers(dest="state_cmd", required=True)
    cmd.add_parser("list", help="list seed state variables")
    inspect_p = cmd.add_parser("inspect", help="print a state-variable definition")
    inspect_p.add_argument("variable_id")
    compute_p = cmd.add_parser("compute", help="compute the last CS snapshot on synthetic bars")
    compute_p.add_argument("variable_id", nargs="?", default="realized_vol_20")


def add_regime_parser(sub: Any) -> None:
    parser = sub.add_parser("regime", help="regime models, classification, and transitions")
    cmd = parser.add_subparsers(dest="regime_cmd", required=True)
    cmd.add_parser("list", help="list seed regime models")
    inspect_p = cmd.add_parser("inspect", help="print a regime-model definition")
    inspect_p.add_argument("item_id")
    for name, help_text in (
        ("fit", "run a regime experiment (walk-forward / rule)"),
        ("classify", "classify synthetic snapshots"),
        ("transitions", "print empirical transition matrix"),
        ("durations", "print run-length statistics"),
        ("changes", "CUSUM change-point flags (not regimes)"),
    ):
        item = cmd.add_parser(name, help=help_text)
        item.add_argument("item_id", nargs="?", default="vol_tercile")
        _add_common(item)


def _add_common(parser: Any) -> None:
    parser.add_argument("--ledger", default="")
    parser.add_argument("--n-days", type=int, default=80)
    parser.add_argument("--family-size", type=int, default=1)


def run_state_command(args: Any) -> int:
    if args.state_cmd == "list":
        rows = [
            {
                "variable_id": item.variable_id,
                "version": item.version,
                "lookback": item.lookback,
                "identity": item.identity_hash(),
                "definition": item.mathematical_definition,
            }
            for item in list_state_variables()
        ]
        print(json.dumps(rows, indent=2))
        return 0
    definition = get_state_variable(args.variable_id)
    if args.state_cmd == "inspect":
        payload = definition.model_dump(mode="json")
        payload["identity_hash"] = definition.identity_hash()
        print(json.dumps(payload, indent=2))
        return 0
    provider = MemoryBarProvider(n_days=80)
    panel = compute_state_panel(provider.all_bars())
    last = panel[-1] if panel else None
    vector = {} if last is None else last.vector()
    print(
        json.dumps(
            {
                "variable_id": definition.variable_id,
                "as_of": None if last is None else last.as_of.isoformat(),
                "value": vector.get(definition.variable_id),
                "snapshot": None if last is None else last.model_dump(mode="json"),
                "note": definition.notes or last.note if last is not None else "",
            },
            indent=2,
            default=str,
        )
    )
    return 0


def run_regime_command(args: Any) -> int:
    if args.regime_cmd == "list":
        rows = [
            {
                "regime_model_id": item.regime_model_id,
                "version": item.version,
                "detector": item.detector.value,
                "n_regimes": item.n_regimes,
                "lifecycle": item.lifecycle.value,
                "identity": item.identity_hash(),
            }
            for item in list_regime_models()
        ]
        print(json.dumps(rows, indent=2))
        return 0
    if args.regime_cmd == "inspect":
        model = get_regime_model(args.item_id)
        payload = model.model_dump(mode="json")
        payload["identity_hash"] = model.identity_hash()
        print(json.dumps(payload, indent=2))
        return 0
    if args.regime_cmd == "fit":
        from quantlab.regimes.experiment import run_named_regime_experiment

        model = get_regime_model(args.item_id)
        predictive = model.detector not in {
            DetectorKind.HMM_SMOOTH,
            DetectorKind.CLUSTER_FULL_SAMPLE,
        }
        try:
            report, run, _snaps, _obs = run_named_regime_experiment(
                args.item_id,
                ledger_path=_ledger_path(args.ledger),
                n_days=args.n_days,
                family_size=args.family_size,
                fabric_root=resolve_fabric_root(),
                append=True,
                predictive=predictive,
            )
        except RegimeError as exc:
            print(json.dumps({"error": str(exc), "blocked": True}))
            return 1
        print(
            json.dumps(
                {
                    "experiment_id": run.id,
                    "regime_model_id": report.regime_model_id,
                    "identity_hash": report.identity_hash,
                    "gate_outcome": report.gate.outcome.value,
                    "data_kind": report.data_kind,
                    "n_labelled": report.n_labelled,
                    "transitions": report.transitions.n_transitions,
                    "integrity": report.integrity,
                    "note": report.note,
                },
                indent=2,
                default=str,
            )
        )
        return 0
    model = get_regime_model(args.item_id)
    provider = MemoryBarProvider(n_days=getattr(args, "n_days", 80))
    snapshots = compute_state_panel(provider.all_bars(), lookback=model.lookback)
    if args.regime_cmd == "changes":
        changes = detect_changes(snapshots)
        print(json.dumps(changes.model_dump(mode="json"), indent=2, default=str))
        return 0
    predictive = model.detector not in {
        DetectorKind.HMM_SMOOTH,
        DetectorKind.CLUSTER_FULL_SAMPLE,
    }
    try:
        observations = classify(model, snapshots, predictive=predictive)
    except RegimeError as exc:
        print(json.dumps({"error": str(exc), "blocked": True}))
        return 1
    if args.regime_cmd == "classify":
        last = observations[-1] if observations else None
        print(
            json.dumps(
                {
                    "regime_model_id": model.regime_model_id,
                    "n": len(observations),
                    "last": None if last is None else last.model_dump(mode="json"),
                    "note": model.notes,
                },
                indent=2,
                default=str,
            )
        )
        return 0
    if args.regime_cmd == "transitions":
        print(json.dumps(transition_matrix(observations).model_dump(mode="json"), indent=2))
        return 0
    print(json.dumps(durations(observations).model_dump(mode="json"), indent=2))
    return 0


def _ledger_path(raw: str) -> Path:
    if raw:
        return Path(raw)
    return Path(get_settings().experiment_ledger_path)
