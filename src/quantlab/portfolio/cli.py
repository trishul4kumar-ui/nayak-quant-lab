"""quantlab portfolio list|inspect|build|risk|exposures|turnover|compare."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quantlab.alpha.ensemble import get_ensemble, list_ensembles
from quantlab.core.config import get_settings
from quantlab.data.fabric.layout import resolve_fabric_root
from quantlab.models.registry import ExperimentLedger
from quantlab.portfolio.spec import get_portfolio_model, list_portfolio_models
from quantlab.research.compare import compare_runs


def add_portfolio_parser(sub: Any) -> None:
    parser = sub.add_parser("portfolio", help="cross-sectional portfolio construction")
    cmd = parser.add_subparsers(dest="portfolio_cmd", required=True)
    cmd.add_parser("list", help="list seed portfolios and ensembles")
    inspect_p = cmd.add_parser("inspect", help="print a portfolio or ensemble definition")
    inspect_p.add_argument("item_id")
    build = cmd.add_parser("build", help="run a seed portfolio experiment")
    build.add_argument("item_id")
    _add_common(build)
    for name, help_text in (
        ("risk", "print risk diagnostics for a ledger experiment"),
        ("exposures", "print exposure diagnostics"),
        ("turnover", "print turnover diagnostics"),
    ):
        item = cmd.add_parser(name, help=help_text)
        item.add_argument("experiment")
        item.add_argument("--ledger", default="")
    compare = cmd.add_parser("compare", help="compare two ledger experiments")
    compare.add_argument("experiment_a")
    compare.add_argument("experiment_b")
    compare.add_argument("--ledger", default="")


def _add_common(parser: Any) -> None:
    parser.add_argument("--ledger", default="")
    parser.add_argument("--n-days", type=int, default=80)
    parser.add_argument("--family-size", type=int, default=1)


def run_portfolio_command(args: Any) -> int:
    cmd = args.portfolio_cmd
    if cmd == "list":
        rows = {
            "portfolios": [
                {
                    "portfolio_id": item.portfolio_id,
                    "version": item.version,
                    "ensemble_id": item.ensemble_id,
                    "constructor": item.constructor.value,
                    "rebalance": item.rebalance.value,
                    "identity": item.identity_hash(),
                }
                for item in list_portfolio_models()
            ],
            "ensembles": [
                {
                    "ensemble_id": item.ensemble_id,
                    "version": item.version,
                    "method": item.method.value,
                    "components": [c.alpha_id for c in item.components],
                    "identity": item.identity_hash(),
                }
                for item in list_ensembles()
            ],
        }
        print(json.dumps(rows, indent=2))
        return 0
    if cmd == "inspect":
        return _inspect(args.item_id)
    if cmd == "build":
        return _build(args)
    if cmd == "compare":
        ledger = ExperimentLedger(_ledger_path(args.ledger))
        left = ledger.get(args.experiment_a)
        right = ledger.get(args.experiment_b)
        if left is None or right is None:
            print(json.dumps({"error": "one or both experiments not found"}))
            return 1
        print(json.dumps(compare_runs([left, right]).model_dump(mode="json"), indent=2))
        return 0
    return _artifact_view(args)


def _inspect(item_id: str) -> int:
    try:
        model = get_portfolio_model(item_id)
        print(json.dumps(model.model_dump(mode="json"), indent=2))
        return 0
    except KeyError:
        pass
    try:
        ensemble = get_ensemble(item_id)
        print(json.dumps(ensemble.model_dump(mode="json"), indent=2))
        return 0
    except KeyError:
        print(json.dumps({"error": f"unknown portfolio or ensemble {item_id}"}))
        return 1


def _build(args: Any) -> int:
    from quantlab.portfolio.experiment import run_model_on_synthetic
    from quantlab.portfolio.spec import ConstructorKind, PortfolioModel

    ledger = _ledger_path(args.ledger)
    item_id = args.item_id
    try:
        model = get_portfolio_model(item_id)
    except KeyError:
        get_ensemble(item_id)
        model = PortfolioModel(
            portfolio_id=f"transient_{item_id}_topn",
            version="1",
            name=f"Top-N from ensemble {item_id}",
            ensemble_id=item_id,
            constructor=ConstructorKind.TOP_N,
            top_n=2,
            family_id="ad_hoc",
            notes="CLI-constructed from ensemble id; not a registered seed",
        )
    report, run, result = run_model_on_synthetic(
        model,
        ledger_path=ledger,
        n_days=args.n_days,
        family_size=args.family_size,
        fabric_root=resolve_fabric_root(),
        append=True,
    )
    payload: dict[str, Any] = {
        "experiment_id": run.id,
        "portfolio_id": report.portfolio_id,
        "ensemble_id": report.ensemble_id,
        "constructor": run.optimizer,
        "gate_outcome": report.gate.outcome.value,
        "data_kind": report.data_kind,
        "infeasible": report.infeasible,
        "integrity": report.integrity,
        "n_rebalances": report.n_rebalances,
        "note": report.note,
    }
    if result is not None:
        payload["total_return"] = result.total_return
        payload["sharpe"] = result.metrics.get("sharpe")
        payload["max_drawdown"] = result.max_drawdown
    if report.last_diagnostics is not None:
        payload["diagnostics"] = report.last_diagnostics.model_dump(mode="json")
    if report.ic is not None:
        payload["spearman_ic"] = report.ic.spearman_mean
    print(json.dumps(payload, indent=2, default=str))
    return 0


def _artifact_view(args: Any) -> int:
    ledger = ExperimentLedger(_ledger_path(args.ledger))
    run = ledger.get(args.experiment)
    if run is None:
        print(json.dumps({"error": "experiment not found"}))
        return 1
    risk = _read_artifact(ledger.path, run.id, "risk")
    if args.portfolio_cmd == "risk":
        print(
            json.dumps(
                risk if risk is not None else {"metrics": run.metrics}, indent=2, default=str
            )
        )
        return 0
    if args.portfolio_cmd == "exposures":
        if isinstance(risk, dict) and "exposures" in risk:
            print(json.dumps(risk["exposures"], indent=2, default=str))
            return 0
        print(
            json.dumps(
                {
                    "gross": run.metrics.get("gross"),
                    "net": run.metrics.get("net"),
                    "hhi": run.metrics.get("hhi"),
                    "beta": "not_tested",
                    "sector": "not_tested",
                },
                indent=2,
            )
        )
        return 0
    print(
        json.dumps(
            {
                "turnover": run.metrics.get("turnover"),
                "mean_turnover": run.metrics.get("mean_turnover"),
                "convention": "0.5 * L1",
            },
            indent=2,
        )
    )
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
