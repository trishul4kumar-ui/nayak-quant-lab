"""quantlab backtest / validate / research commands. Same parser as the rest of the CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from quantlab.core.config import get_settings
from quantlab.data.fabric.layout import resolve_fabric_root
from quantlab.models.registry import ExperimentLedger
from quantlab.research.compare import compare_runs
from quantlab.research.pipeline import run_momentum_validation, run_momentum_vertical_slice
from quantlab.research.report import format_validation_report
from quantlab.research.suite import ValidationConfig


def add_research_parsers(sub: Any) -> None:
    backtest = sub.add_parser("backtest", help="run or report a next-bar backtest")
    backtest_sub = backtest.add_subparsers(dest="backtest_cmd", required=True)
    run = backtest_sub.add_parser("run", help="run the synthetic momentum slice")
    _add_common(run)
    report = backtest_sub.add_parser("report", help="print a saved experiment")
    report.add_argument("experiment")
    report.add_argument("--ledger", default="")

    validate = sub.add_parser("validate", help="research-grade validation suite")
    validate_sub = validate.add_subparsers(dest="validate_cmd", required=True)
    for name, help_text in (
        ("run", "full validation suite"),
        ("walk-forward", "walk-forward windows and OOS metrics"),
        ("robustness", "cost, parameter, and regime diagnostics"),
        ("statistics", "bootstrap / sign-flip diagnostics"),
    ):
        parser = validate_sub.add_parser(name, help=help_text)
        _add_common(parser)

    research = sub.add_parser("research", help="compare experiments and inspect the gate")
    research_sub = research.add_subparsers(dest="research_cmd", required=True)
    compare = research_sub.add_parser("compare", help="compare two ledger experiments")
    compare.add_argument("experiment_a")
    compare.add_argument("experiment_b")
    compare.add_argument("--ledger", default="")
    gate = research_sub.add_parser("gate", help="print research-gate outcome")
    gate.add_argument("experiment")
    gate.add_argument("--ledger", default="")
    feature = research_sub.add_parser("feature", help="feature IC / quantile / decay experiment")
    feature.add_argument("feature_id")
    _add_common(feature)
    feature.add_argument("--horizon", type=int, default=1)
    feature.add_argument("--family-size", type=int, default=1)
    alpha = research_sub.add_parser("alpha", help="alpha combination IC experiment")
    alpha.add_argument("alpha_id")
    _add_common(alpha)
    alpha.add_argument("--family-size", type=int, default=1)
    ensemble = research_sub.add_parser("ensemble", help="inspect an alpha ensemble and its IC")
    ensemble.add_argument("ensemble_id")
    _add_common(ensemble)
    portfolio = research_sub.add_parser("portfolio", help="run a seed portfolio experiment")
    portfolio.add_argument("portfolio_id")
    _add_common(portfolio)
    portfolio.add_argument("--family-size", type=int, default=1)
    factor = research_sub.add_parser("factor", help="factor IC experiment")
    factor.add_argument("factor_id")
    _add_common(factor)
    factor.add_argument("--family-size", type=int, default=1)
    factor_corr = research_sub.add_parser(
        "factor-correlation",
        help="pairwise factor-factor correlation",
    )
    factor_corr.add_argument("factor_id", nargs="?", default="style_momentum_20")
    factor_corr.add_argument("--other", default="style_volatility_20")
    _add_common(factor_corr)
    regime = research_sub.add_parser("regime", help="regime classification experiment")
    regime.add_argument("regime_model_id")
    _add_common(regime)
    regime.add_argument("--family-size", type=int, default=1)
    regime_alpha = research_sub.add_parser(
        "regime-alpha",
        help="factor IC split by contemporaneous regime",
    )
    regime_alpha.add_argument("alpha_id", nargs="?", default="style_momentum_20")
    regime_alpha.add_argument("regime_model_id", nargs="?", default="vol_tercile")
    _add_common(regime_alpha)
    regime_risk = research_sub.add_parser(
        "regime-risk",
        help="covariance snapshot inside a named regime",
    )
    regime_risk.add_argument("portfolio_id", nargs="?", default="mom20_topn")
    regime_risk.add_argument("regime_model_id", nargs="?", default="vol_tercile")
    _add_common(regime_risk)
    regime_corr = research_sub.add_parser(
        "regime-correlation",
        help="state-variable expanding z-score correlation",
    )
    _add_common(regime_corr)
    adaptive = research_sub.add_parser("adaptive", help="adaptive prequential experiment")
    adaptive.add_argument("adaptive_model_id")
    _add_common(adaptive)
    adaptive.add_argument("--family-size", type=int, default=1)
    alpha_decay = research_sub.add_parser("alpha-decay", help="IC half-life of an alpha")
    alpha_decay.add_argument("alpha_id", nargs="?", default="rank_momentum_20")
    _add_common(alpha_decay)
    adaptive_cmp = research_sub.add_parser(
        "adaptive-compare",
        help="static vs rolling vs ewma vs ensemble",
    )
    _add_common(adaptive_cmp)
    research_model = research_sub.add_parser("model", help="statistical-model walk-forward")
    research_model.add_argument("model_id", nargs="?", default="ols_mom")
    _add_common(research_model)
    research_model.add_argument("--family-size", type=int, default=1)
    model_cmp = research_sub.add_parser(
        "model-compare",
        help="no-signal vs alpha vs ols vs ridge vs tree",
    )
    _add_common(model_cmp)
    model_stab = research_sub.add_parser("model-stability", help="model coefficient stability")
    model_stab.add_argument("model_id", nargs="?", default="ols_mom")
    _add_common(model_stab)
    meta_alpha = research_sub.add_parser("meta-alpha", help="OLS/ridge meta-alpha walk-forward")
    meta_alpha.add_argument("ensemble_id", nargs="?", default="meta_ols_mom")
    _add_common(meta_alpha)
    meta_alpha.add_argument("--family-size", type=int, default=1)
    stacking = research_sub.add_parser("stacking", help="walk-forward stacking experiment")
    stacking.add_argument("ensemble_id", nargs="?", default="ridge_stack_mom")
    _add_common(stacking)
    stacking.add_argument("--family-size", type=int, default=1)
    ens_div = research_sub.add_parser(
        "ensemble-diversity",
        help="combination-ensemble redundancy diagnostics",
    )
    ens_div.add_argument("ensemble_id", nargs="?", default="ew_mom_5_20")
    _add_common(ens_div)
    ens_stab = research_sub.add_parser(
        "ensemble-stability",
        help="combination-ensemble weight stability",
    )
    ens_stab.add_argument("ensemble_id", nargs="?", default="roll_ic_mom")
    _add_common(ens_stab)
    ens_cmp = research_sub.add_parser(
        "ensemble-compare",
        help="equal vs static vs correlation-aware vs stack",
    )
    _add_common(ens_cmp)
    execution = research_sub.add_parser("execution", help="execution-research simulation")
    execution.add_argument("model_id", nargs="?", default="exec_base")
    _add_common(execution)
    execution_cost = research_sub.add_parser("execution-cost", help="execution cost attribution")
    execution_cost.add_argument("model_id", nargs="?", default="exec_base")
    _add_common(execution_cost)
    execution_frag = research_sub.add_parser(
        "execution-fragility", help="execution fragility score"
    )
    execution_frag.add_argument("model_id", nargs="?", default="exec_base")
    _add_common(execution_frag)
    capacity = research_sub.add_parser("capacity", help="notional capacity scenarios")
    capacity.add_argument("model_id", nargs="?", default="exec_base")
    _add_common(capacity)
    from quantlab.orchestration.cli import add_research_orchestration_parsers

    add_research_orchestration_parsers(research_sub)
    from quantlab.discovery.cli import add_research_discovery_parsers

    add_research_discovery_parsers(research_sub)
    from quantlab.knowledge.cli import add_research_knowledge_parsers

    add_research_knowledge_parsers(research_sub)
    from quantlab.capital.cli import add_research_capital_parsers

    add_research_capital_parsers(research_sub)
    from quantlab.paper_oms.cli import add_research_paper_parsers

    add_research_paper_parsers(research_sub)
    from quantlab.monitoring.cli import add_research_monitor_parsers

    add_research_monitor_parsers(research_sub)
    from quantlab.tca.cli import add_research_tca_parsers

    add_research_tca_parsers(research_sub)
    from quantlab.econometrics.cli import add_research_econometrics_parsers

    add_research_econometrics_parsers(research_sub)
    from quantlab.certification.cli import add_research_certification_parsers

    add_research_certification_parsers(research_sub)
    from quantlab.shadow.cli import add_research_shadow_parsers

    add_research_shadow_parsers(research_sub)
    from quantlab.release.cli import add_research_release_parsers

    add_research_release_parsers(research_sub)
    from quantlab.broker_gateway.cli import add_research_broker_parsers

    add_research_broker_parsers(research_sub)
    from quantlab.realtime_data.cli import add_research_realtime_parsers

    add_research_realtime_parsers(research_sub)
    from quantlab.realtime_decision.cli import add_research_realtime_decision_parsers

    add_research_realtime_decision_parsers(research_sub)
    from quantlab.digital_twin.cli import add_research_twin_parsers

    add_research_twin_parsers(research_sub)
    alpha_corr = research_sub.add_parser(
        "alpha-correlation",
        help="pairwise ensemble-component correlation",
    )
    alpha_corr.add_argument("--ensemble", default="mom_5_20")
    _add_common(alpha_corr)
    for name, help_text in (
        ("ic", "information coefficient vs forward return"),
        ("quantiles", "quantile buckets vs forward return"),
        ("decay", "predictive IC decay across horizons"),
    ):
        parser = research_sub.add_parser(name, help=help_text)
        parser.add_argument("--feature", default="momentum_20")
        _add_common(parser)
        parser.add_argument("--horizon", type=int, default=1)
    corr = research_sub.add_parser("correlation", help="feature-feature correlation")
    corr.add_argument("--feature-a", default="momentum_20")
    corr.add_argument("--feature-b", default="rolling_std_20")
    _add_common(corr)


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--ledger", default="")
    parser.add_argument("--n-days", type=int, default=80)
    parser.add_argument("--lookback", type=int, default=20)
    parser.add_argument("--top-n", type=int, default=2)
    parser.add_argument("--cost-bps", type=float, default=10.0)


def run_research_command(args: argparse.Namespace) -> int:
    if args.cmd == "backtest":
        return _backtest(args)
    if args.cmd == "validate":
        return _validate(args)
    if args.cmd == "research":
        return _research(args)
    raise ValueError(f"unknown command {args.cmd}")


def _ledger_path(raw: str) -> Path:
    if raw:
        return Path(raw)
    return Path(get_settings().experiment_ledger_path)


def _backtest(args: argparse.Namespace) -> int:
    if args.backtest_cmd == "run":
        result, run = run_momentum_vertical_slice(
            ledger_path=_ledger_path(args.ledger),
            n_days=args.n_days,
            lookback=args.lookback,
            top_n=args.top_n,
            cost_bps=args.cost_bps,
            fabric_root=resolve_fabric_root(),
        )
        print(
            json.dumps(
                {
                    "experiment_id": run.id,
                    "config_hash": run.config_hash,
                    "data_kind": run.data_kind,
                    "total_return": result.total_return,
                    "sharpe": result.metrics.get("sharpe"),
                    "max_drawdown": result.max_drawdown,
                    "integrity": result.integrity,
                    "live_trading": False,
                },
                indent=2,
            )
        )
        return 0
    found = ExperimentLedger(_ledger_path(args.ledger)).get(args.experiment)
    if found is None:
        print(json.dumps({"error": "experiment not found"}))
        return 1
    print(json.dumps(found.model_dump(mode="json"), indent=2))
    return 0


def _validate(args: argparse.Namespace) -> int:
    ledger = _ledger_path(args.ledger)
    artifacts = ledger.parent / "artifacts"
    result, run, report = run_momentum_validation(
        ledger_path=ledger,
        n_days=args.n_days,
        lookback=args.lookback,
        top_n=args.top_n,
        cost_bps=args.cost_bps,
        fabric_root=resolve_fabric_root(),
        artifacts_dir=artifacts,
        config=ValidationConfig(lookback=args.lookback, top_n=args.top_n, cost_bps=args.cost_bps),
    )
    cmd = args.validate_cmd
    if cmd == "walk-forward":
        payload = report.walk_forward.model_dump(mode="json")
    elif cmd == "robustness":
        payload = report.robustness.model_dump(mode="json")
    elif cmd == "statistics":
        payload = report.statistics.model_dump(mode="json")
    else:
        payload = {
            "experiment_id": run.id,
            "gate": report.gate.model_dump(mode="json"),
            "data_kind": report.data_kind,
            "oos_windows": report.oos_windows,
            "oos_sharpe": report.oos_sharpe,
            "config_hash": report.config_hash,
            "integrity": result.integrity,
            "text": format_validation_report(report),
        }
    print(json.dumps(payload, indent=2, default=str))
    return 0


def _research(args: argparse.Namespace) -> int:
    ledger = ExperimentLedger(_ledger_path(args.ledger))
    if args.research_cmd == "compare":
        left = ledger.get(args.experiment_a)
        right = ledger.get(args.experiment_b)
        if left is None or right is None:
            print(json.dumps({"error": "one or both experiments not found"}))
            return 1
        print(json.dumps(compare_runs([left, right]).model_dump(mode="json"), indent=2))
        return 0
    if args.research_cmd == "gate":
        run = ledger.get(args.experiment)
        if run is None:
            print(json.dumps({"error": "experiment not found"}))
            return 1
        print(
            json.dumps(
                {
                    "experiment_id": run.id,
                    "gate_outcome": run.gate_outcome,
                    "gate_reasons": run.gate_reasons,
                    "validation": run.validation,
                    "data_kind": run.data_kind,
                },
                indent=2,
            )
        )
        return 0
    if args.research_cmd in {"ensemble", "portfolio", "alpha-correlation"}:
        return _research_portfolio_commands(args)
    if args.research_cmd in {"factor", "factor-correlation"}:
        return _research_factor_commands(args)
    if args.research_cmd in {"regime", "regime-alpha", "regime-risk", "regime-correlation"}:
        return _research_regime_commands(args)
    if args.research_cmd in {"adaptive", "alpha-decay", "adaptive-compare"}:
        return _research_adaptive_commands(args)
    if args.research_cmd in {"model", "model-compare", "model-stability"}:
        return _research_model_commands(args)
    if args.research_cmd in {
        "meta-alpha",
        "stacking",
        "ensemble-diversity",
        "ensemble-stability",
        "ensemble-compare",
    }:
        return _research_ensemble_meta_commands(args)
    if args.research_cmd in {
        "execution",
        "execution-cost",
        "execution-fragility",
        "capacity",
    }:
        return _research_execution_commands(args)
    if args.research_cmd in {
        "discover",
        "replicate",
        "falsify",
        "ablation",
        "sensitivity",
        "grid",
        "family",
        "multiple-testing",
        "lineage",
        "degrees-of-freedom",
        "pareto",
        "status",
    }:
        from quantlab.orchestration.cli import run_research_orchestration_command

        return run_research_orchestration_command(args)
    if args.research_cmd in {
        "symbolic",
        "genetic",
        "alpha-discovery",
        "novelty",
        "expression",
        "discovery-family",
    }:
        from quantlab.discovery.cli import run_research_discovery_command

        return run_research_discovery_command(args)
    if args.research_cmd in {
        "knowledge",
        "genealogy",
        "dead-ends",
        "replication",
        "contradictions",
        "similarity",
        "evidence",
        "alpha-family",
    }:
        from quantlab.knowledge.cli import run_research_knowledge_command

        return run_research_knowledge_command(args)
    if args.research_cmd in {
        "capital",
        "allocation",
        "decision",
        "risk-budget",
        "sizing",
        "capital-efficiency",
        "allocation-stability",
    }:
        from quantlab.capital.cli import run_research_capital_command

        return run_research_capital_command(args)
    if args.research_cmd in {
        "paper-oms",
        "paper-execution",
        "order-lifecycle",
        "reconciliation",
        "paper-tca",
    }:
        from quantlab.paper_oms.cli import run_research_paper_command

        return run_research_paper_command(args)
    if args.research_cmd in {
        "performance",
        "attribution",
        "portfolio-drift",
        "performance-feedback",
    }:
        from quantlab.monitoring.cli import run_research_monitor_command

        return run_research_monitor_command(args)
    if args.research_cmd in {
        "tca",
        "implementation-shortfall",
        "execution-calibration",
        "tca-capacity",
        "tca-fragility",
    }:
        from quantlab.tca.cli import run_research_tca_command

        return run_research_tca_command(args)
    if args.research_cmd in {
        "econometrics",
        "stationarity",
        "granger",
        "cointegration",
        "structural-break",
        "causal",
        "panel",
    }:
        from quantlab.econometrics.cli import run_research_econometrics_command

        return run_research_econometrics_command(args)
    if args.research_cmd in {
        "model-risk",
        "validation",
        "certification",
        "reproducibility",
        "readiness",
        "governance",
    }:
        from quantlab.certification.cli import run_research_certification_command

        return run_research_certification_command(args)
    if args.research_cmd in {
        "shadow",
        "paper-production",
        "shadow-execution",
        "decision-drift",
        "production-fragility",
        "shadow-tca",
        "shadow-reconciliation",
    }:
        from quantlab.shadow.cli import run_research_shadow_command

        return run_research_shadow_command(args)
    if args.research_cmd in {
        "live-certification",
        "live-readiness",
        "promotion",
        "release-gate",
        "certification-audit",
    }:
        from quantlab.release.cli import run_research_release_command

        return run_research_release_command(args)
    if args.research_cmd in {
        "broker",
        "account-state",
        "account-reconciliation",
        "broker-health",
        "broker-audit",
    }:
        from quantlab.broker_gateway.cli import run_research_broker_command

        return run_research_broker_command(args)
    if args.research_cmd in {
        "realtime-data",
        "market-state",
        "data-freshness",
        "sequence-integrity",
        "realtime-replay",
    }:
        from quantlab.realtime_data.cli import run_research_realtime_command

        return run_research_realtime_command(args)
    if args.research_cmd in {
        "realtime",
        "realtime-decision",
        "decision-replay",
        "decision-stability",
        "decision-abstention",
    }:
        from quantlab.realtime_decision.cli import run_research_realtime_decision_command

        return run_research_realtime_decision_command(args)
    if args.research_cmd in {
        "digital-twin",
        "twin-validation",
        "deterministic-replay",
        "failure-injection",
        "twin-recovery",
        "counterfactual",
        "twin-drift",
    }:
        from quantlab.digital_twin.cli import run_research_twin_command

        return run_research_twin_command(args)
    return _research_feature_commands(args)


def _research_portfolio_commands(args: argparse.Namespace) -> int:
    from quantlab.alpha.ensemble import get_ensemble
    from quantlab.portfolio.experiment import (
        run_named_ensemble_experiment,
        run_named_portfolio_experiment,
    )

    ledger = _ledger_path(args.ledger)
    if args.research_cmd == "ensemble":
        ensemble = get_ensemble(args.ensemble_id)
        _scores, ic, corr = run_named_ensemble_experiment(
            args.ensemble_id,
            ledger_path=ledger,
            n_days=args.n_days,
            fabric_root=resolve_fabric_root(),
        )
        print(
            json.dumps(
                {
                    "ensemble": ensemble.model_dump(mode="json"),
                    "identity_hash": ensemble.identity_hash(),
                    "ic": ic.model_dump(mode="json"),
                    "correlation": [p.model_dump(mode="json") for p in corr],
                    "note": "ensemble IC is not a promotion score",
                },
                indent=2,
                default=str,
            )
        )
        return 0
    if args.research_cmd == "portfolio":
        report, run, result = run_named_portfolio_experiment(
            args.portfolio_id,
            ledger_path=ledger,
            n_days=args.n_days,
            family_size=getattr(args, "family_size", 1),
            fabric_root=resolve_fabric_root(),
        )
        payload: dict[str, Any] = {
            "experiment_id": run.id,
            "portfolio_id": report.portfolio_id,
            "ensemble_id": report.ensemble_id,
            "gate_outcome": report.gate.outcome.value,
            "data_kind": report.data_kind,
            "infeasible": report.infeasible,
            "integrity": report.integrity,
            "n_rebalances": report.n_rebalances,
            "spearman_ic": None if report.ic is None else report.ic.spearman_mean,
            "note": report.note,
        }
        if result is not None:
            payload["total_return"] = result.total_return
            payload["sharpe"] = result.metrics.get("sharpe")
        print(json.dumps(payload, indent=2, default=str))
        return 0
    _scores, _ic, corr = run_named_ensemble_experiment(
        args.ensemble,
        ledger_path=ledger,
        n_days=args.n_days,
        fabric_root=resolve_fabric_root(),
    )
    print(
        json.dumps(
            {"ensemble": args.ensemble, "pairs": [p.model_dump(mode="json") for p in corr]},
            indent=2,
        )
    )
    return 0


def _research_factor_commands(args: argparse.Namespace) -> int:
    from quantlab.factors.experiment import (
        factor_pair_correlation,
        run_named_factor_experiment,
    )
    from quantlab.research.pipeline import load_synthetic_frame

    ledger = _ledger_path(args.ledger)
    if args.research_cmd == "factor-correlation":
        frame = load_synthetic_frame(
            n_days=args.n_days, ledger_path=ledger, fabric_root=resolve_fabric_root()
        )
        pair = factor_pair_correlation(args.factor_id, args.other, frame.bars)
        print(json.dumps(pair.model_dump(mode="json"), indent=2))
        return 0
    report, run, _panel = run_named_factor_experiment(
        args.factor_id,
        ledger_path=ledger,
        n_days=args.n_days,
        family_size=getattr(args, "family_size", 1),
        fabric_root=resolve_fabric_root(),
    )
    print(
        json.dumps(
            {
                "experiment_id": run.id,
                "factor_id": report.factor_id,
                "identity_hash": report.identity_hash,
                "gate_outcome": report.gate.outcome.value,
                "data_kind": report.data_kind,
                "integrity": report.integrity,
                "ic": report.ic.model_dump(mode="json"),
                "quality": report.quality.model_dump(mode="json"),
                "observation": report.observation.model_dump(mode="json"),
                "note": report.note,
            },
            indent=2,
            default=str,
        )
    )
    return 0


def _research_regime_commands(args: argparse.Namespace) -> int:
    from quantlab.regimes.engine import compute_state_panel
    from quantlab.regimes.experiment import run_named_regime_experiment
    from quantlab.regimes.normalize import expanding_zscore, series_of
    from quantlab.research.pipeline import load_synthetic_frame

    ledger = _ledger_path(args.ledger)
    if args.research_cmd == "regime-correlation":
        frame = load_synthetic_frame(
            n_days=args.n_days, ledger_path=ledger, fabric_root=resolve_fabric_root()
        )
        snaps = compute_state_panel(frame.bars)
        vol = expanding_zscore(series_of(snaps, "realized_vol_20"))
        disp = expanding_zscore(series_of(snaps, "dispersion_cs"))
        paired = [(a, b) for a, b in zip(vol, disp, strict=True) if a is not None and b is not None]
        n = len(paired)
        corr = None
        if n >= 8:
            mx = sum(a for a, _ in paired) / n
            my = sum(b for _, b in paired) / n
            num = sum((a - mx) * (b - my) for a, b in paired)
            denx = sum((a - mx) ** 2 for a, _ in paired) ** 0.5
            deny = sum((b - my) ** 2 for _, b in paired) ** 0.5
            if denx > 0 and deny > 0:
                corr = num / (denx * deny)
        print(
            json.dumps(
                {
                    "feature_a": "realized_vol_20",
                    "feature_b": "dispersion_cs",
                    "pearson": corr,
                    "n": n,
                    "note": "expanding z-scores through T; not a forecast",
                },
                indent=2,
            )
        )
        return 0
    model_id = args.regime_model_id
    report, run, _snaps, observations = run_named_regime_experiment(
        model_id,
        ledger_path=ledger,
        n_days=args.n_days,
        family_size=getattr(args, "family_size", 1),
        fabric_root=resolve_fabric_root(),
    )
    if args.research_cmd == "regime-alpha":
        print(
            json.dumps(
                {
                    "experiment_id": run.id,
                    "alpha_id": args.alpha_id,
                    "regime_model_id": model_id,
                    "slices": [row.model_dump(mode="json") for row in report.conditional_ic],
                    "gate_outcome": report.gate.outcome.value,
                    "note": "conditional IC is association, not alpha",
                },
                indent=2,
                default=str,
            )
        )
        return 0
    if args.research_cmd == "regime-risk":
        print(
            json.dumps(
                {
                    "experiment_id": run.id,
                    "portfolio_id": args.portfolio_id,
                    "regime_model_id": model_id,
                    "slices": [row.model_dump(mode="json") for row in report.conditional_cov],
                    "gate_outcome": report.gate.outcome.value,
                    "n_labelled": report.n_labelled,
                    "note": "regime-conditional Σ is not a forecast",
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
                "regime_model_id": report.regime_model_id,
                "identity_hash": report.identity_hash,
                "gate_outcome": report.gate.outcome.value,
                "data_kind": report.data_kind,
                "n_labelled": report.n_labelled,
                "transitions": report.transitions.model_dump(mode="json"),
                "durations": report.durations.model_dump(mode="json"),
                "integrity": report.integrity,
                "n_observations": len(observations),
                "note": report.note,
            },
            indent=2,
            default=str,
        )
    )
    return 0


def _research_adaptive_commands(args: argparse.Namespace) -> int:
    from quantlab.adaptive.cli import run_adaptive_command

    if args.research_cmd == "alpha-decay":
        return run_adaptive_command(
            argparse.Namespace(adaptive_cmd="decay", alpha_id=args.alpha_id)
        )
    if args.research_cmd == "adaptive-compare":
        return run_adaptive_command(
            argparse.Namespace(
                adaptive_cmd="compare",
                item_a="static_mom20",
                item_b="ensemble_ic_mom",
                ledger=args.ledger,
                n_days=args.n_days,
            )
        )
    return run_adaptive_command(
        argparse.Namespace(
            adaptive_cmd="run",
            item_id=args.adaptive_model_id,
            ledger=args.ledger,
            n_days=args.n_days,
            family_size=getattr(args, "family_size", 1),
        )
    )


def _research_model_commands(args: argparse.Namespace) -> int:
    from quantlab.learning.cli import run_model_command

    if args.research_cmd == "model-compare":
        return run_model_command(
            argparse.Namespace(
                model_cmd="compare",
                item_a="ols_mom",
                item_b="ridge_mom",
                ledger=args.ledger,
                n_days=args.n_days,
            )
        )
    if args.research_cmd == "model-stability":
        return run_model_command(
            argparse.Namespace(
                model_cmd="stability",
                item_id=args.model_id,
                ledger=args.ledger,
                n_days=args.n_days,
                family_size=getattr(args, "family_size", 1),
            )
        )
    return run_model_command(
        argparse.Namespace(
            model_cmd="evaluate",
            item_id=args.model_id,
            ledger=args.ledger,
            n_days=args.n_days,
            family_size=getattr(args, "family_size", 1),
        )
    )


def _research_ensemble_meta_commands(args: argparse.Namespace) -> int:
    from quantlab.ensemble.cli import run_ensemble_command

    if args.research_cmd == "ensemble-compare":
        return run_ensemble_command(
            argparse.Namespace(
                ensemble_cmd="compare",
                item_a="ew_mom_5_20",
                item_b="ridge_stack_mom",
                ledger=args.ledger,
                n_days=args.n_days,
            )
        )
    cmd = {
        "meta-alpha": "evaluate",
        "stacking": "evaluate",
        "ensemble-diversity": "diversity",
        "ensemble-stability": "stability",
    }[args.research_cmd]
    item = getattr(args, "ensemble_id", "ew_mom_5_20")
    return run_ensemble_command(
        argparse.Namespace(
            ensemble_cmd=cmd,
            item_id=item,
            ledger=args.ledger,
            n_days=args.n_days,
            family_size=getattr(args, "family_size", 1),
        )
    )


def _research_execution_commands(args: argparse.Namespace) -> int:
    from quantlab.execution_research.cli import run_execution_command

    cmd = {
        "execution": "simulate",
        "execution-cost": "costs",
        "execution-fragility": "stress",
        "capacity": "capacity",
    }[args.research_cmd]
    return run_execution_command(
        argparse.Namespace(
            execution_cmd=cmd,
            item_id=getattr(args, "model_id", "exec_base"),
            ledger=args.ledger,
            n_days=args.n_days,
            family_size=1,
            capital=1_000_000.0,
            scenario="",
        )
    )


def _research_feature_commands(args: argparse.Namespace) -> int:
    from quantlab.alpha.experiment import run_named_alpha_experiment, run_named_feature_experiment
    from quantlab.features.correlation import correlate_panels
    from quantlab.features.engine import compute_panel, session_calendar
    from quantlab.features.registry import get_feature
    from quantlab.research.pipeline import load_synthetic_frame

    ledger = _ledger_path(args.ledger)
    if args.research_cmd == "correlation":
        frame = load_synthetic_frame(
            n_days=args.n_days, ledger_path=ledger, fabric_root=resolve_fabric_root()
        )
        dates = session_calendar(frame.bars)
        left = compute_panel(get_feature(args.feature_a), frame.bars, dates)
        right = compute_panel(get_feature(args.feature_b), frame.bars, dates)
        pair = correlate_panels(args.feature_a, left, args.feature_b, right)
        print(json.dumps(pair.model_dump(mode="json"), indent=2))
        return 0
    if args.research_cmd == "alpha":
        report, run = run_named_alpha_experiment(
            args.alpha_id,
            ledger_path=ledger,
            n_days=args.n_days,
            family_size=args.family_size,
            fabric_root=resolve_fabric_root(),
        )
        print(_feature_payload(report, run, "ic"))
        return 0
    feature_id = args.feature_id if args.research_cmd == "feature" else args.feature
    report, run = run_named_feature_experiment(
        feature_id,
        ledger_path=ledger,
        n_days=args.n_days,
        horizon=getattr(args, "horizon", 1),
        family_size=getattr(args, "family_size", 1),
        fabric_root=resolve_fabric_root(),
        append=args.research_cmd == "feature",
    )
    if args.research_cmd == "quantiles":
        print(_feature_payload(report, run, "quantiles"))
        return 0
    if args.research_cmd == "decay":
        print(_feature_payload(report, run, "decay"))
        return 0
    print(_feature_payload(report, run, "ic"))
    return 0


def _feature_payload(report: Any, run: Any, section: str) -> str:
    body: dict[str, Any] = {
        "experiment_id": run.id,
        "feature_id": report.feature_id,
        "identity_hash": report.identity_hash,
        "gate_outcome": report.gate.outcome.value,
        "data_kind": report.data_kind,
        "integrity": report.integrity,
        "n_aligned": report.n_aligned,
        "note": report.note,
    }
    if section == "quantiles":
        body["quantiles"] = report.quantiles.model_dump(mode="json")
    elif section == "decay":
        body["decay"] = report.decay.model_dump(mode="json")
    else:
        body["ic"] = report.ic.model_dump(mode="json")
    return json.dumps(body, indent=2, default=str)
