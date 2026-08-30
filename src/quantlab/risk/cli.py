"""quantlab risk list|inspect|compute|exposure|attribution|covariance|stress."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quantlab.core.config import get_settings
from quantlab.data.fabric.layout import resolve_fabric_root
from quantlab.models.registry import ExperimentLedger
from quantlab.portfolio.spec import get_portfolio_model
from quantlab.risk.model import get_risk_model, list_risk_models


def add_risk_parser(sub: Any) -> None:
    parser = sub.add_parser("risk", help="research risk models, exposures, and stress")
    cmd = parser.add_subparsers(dest="risk_cmd", required=True)
    cmd.add_parser("list", help="list seed research risk models")
    inspect_p = cmd.add_parser("inspect", help="print a risk-model definition")
    inspect_p.add_argument("item_id")
    compute = cmd.add_parser("compute", help="run a research risk snapshot")
    compute.add_argument("portfolio")
    _add_common(compute)
    exposure = cmd.add_parser("exposure", help="factor exposures for a portfolio snapshot")
    exposure.add_argument("portfolio")
    _add_common(exposure)
    for name, help_text in (
        ("attribution", "print factor attribution artifacts"),
        ("covariance", "print covariance artifacts"),
        ("stress", "print stress artifacts"),
    ):
        item = cmd.add_parser(name, help=help_text)
        item.add_argument("experiment")
        item.add_argument("--ledger", default="")


def _add_common(parser: Any) -> None:
    parser.add_argument("--ledger", default="")
    parser.add_argument("--n-days", type=int, default=80)
    parser.add_argument("--family-size", type=int, default=1)
    parser.add_argument("--model", default="sample_cs")


def run_risk_command(args: Any) -> int:
    cmd = args.risk_cmd
    if cmd == "list":
        rows = [
            {
                "risk_model_id": item.risk_model_id,
                "version": item.version,
                "estimator": item.covariance_estimator,
                "lookback": item.covariance_lookback,
                "factors": item.factor_ids,
                "identity": item.identity_hash(),
            }
            for item in list_risk_models()
        ]
        print(json.dumps(rows, indent=2))
        return 0
    if cmd == "inspect":
        try:
            spec = get_risk_model(args.item_id)
        except KeyError:
            print(json.dumps({"error": f"unknown risk model {args.item_id}"}))
            return 1
        payload = spec.model_dump(mode="json")
        payload["identity_hash"] = spec.identity_hash()
        print(json.dumps(payload, indent=2))
        return 0
    if cmd in {"compute", "exposure"}:
        return _compute(args)
    return _artifact_view(args)


def _compute(args: Any) -> int:
    from quantlab.risk.experiment import run_named_risk_experiment

    model_id = args.model
    portfolio_id = ""
    try:
        get_risk_model(args.portfolio)
        model_id = args.portfolio
    except KeyError:
        try:
            get_portfolio_model(args.portfolio)
            portfolio_id = args.portfolio
        except KeyError:
            portfolio_id = args.portfolio
    report, run = run_named_risk_experiment(
        model_id,
        ledger_path=_ledger_path(args.ledger),
        n_days=args.n_days,
        family_size=args.family_size,
        fabric_root=resolve_fabric_root(),
        append=True,
        portfolio_id=portfolio_id,
    )
    if args.risk_cmd == "exposure":
        print(
            json.dumps(
                {
                    "experiment_id": run.id,
                    "portfolio": portfolio_id or args.portfolio,
                    "exposures": report.exposures,
                    "missing": report.missing_exposures,
                    "beta_mean": report.beta_mean,
                    "note": report.note,
                },
                indent=2,
                default=str,
            )
        )
        return 0
    print(
        json.dumps(
            {
                "experiment_id": run.id,
                "risk_model_id": report.risk_model_id,
                "identity_hash": report.identity_hash,
                "gate_outcome": report.gate.outcome.value,
                "data_kind": report.data_kind,
                "estimated_volatility": report.estimated_volatility,
                "condition_number": report.condition_number,
                "psd": report.psd,
                "exposures": report.exposures,
                "beta_mean": report.beta_mean,
                "stress": [item.model_dump(mode="json") for item in report.stress],
                "integrity": report.integrity,
                "note": report.note,
            },
            indent=2,
            default=str,
        )
    )
    return 0


def _artifact_view(args: Any) -> int:
    ledger = ExperimentLedger(_ledger_path(args.ledger))
    run = ledger.get(args.experiment)
    if run is None:
        print(json.dumps({"error": "experiment not found"}))
        return 1
    name = {"attribution": "attribution", "covariance": "covariance", "stress": "stress"}[
        args.risk_cmd
    ]
    body = _read_artifact(ledger.path, run.id, name)
    if body is None:
        print(
            json.dumps(
                {
                    "experiment_id": run.id,
                    "risk_model_id": run.risk_model_id,
                    "metrics": run.metrics,
                    "note": f"no {name} artifact; run quantlab risk compute first",
                },
                indent=2,
            )
        )
        return 0
    print(json.dumps(body, indent=2, default=str))
    return 0


def _read_artifact(ledger: Path, experiment_id: str, name: str) -> Any | None:
    path = ledger.parent / "artifacts" / experiment_id / f"{name}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _ledger_path(raw: str) -> Path:
    if raw:
        return Path(raw)
    return Path(get_settings().experiment_ledger_path)
