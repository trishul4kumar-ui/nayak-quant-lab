from __future__ import annotations

import argparse
import json
from pathlib import Path

from quantlab.adaptive.cli import add_adaptive_parser, run_adaptive_command
from quantlab.agents.cli import add_agents_parser, run_agents_command
from quantlab.alpha.cli import add_alpha_parser, run_alpha_command
from quantlab.broker_gateway.cli import add_broker_parser, run_broker_command
from quantlab.capital.cli import add_capital_parser, run_capital_command
from quantlab.certification.cli import add_validation_parser, run_validation_command
from quantlab.core.config import get_settings
from quantlab.core.logging import configure_logging
from quantlab.data.cli import add_data_parser, run_data_command
from quantlab.data.fabric.layout import resolve_fabric_root
from quantlab.digital_twin.cli import add_twin_parser, run_twin_command
from quantlab.discovery.cli import add_discovery_parser, run_discovery_command
from quantlab.econometrics.cli import add_econometrics_parser, run_econometrics_command
from quantlab.ensemble.cli import add_ensemble_parser, run_ensemble_command
from quantlab.execution_authorization.cli import (
    add_execution_authorization_parser,
    run_execution_authorization_command,
)
from quantlab.execution_research.cli import add_execution_parser, run_execution_command
from quantlab.factors.cli import add_factor_parser, run_factor_command
from quantlab.features.cli import add_feature_parser, run_feature_command
from quantlab.knowledge.cli import add_knowledge_parser, run_knowledge_command
from quantlab.learning.cli import add_model_parser, run_model_command
from quantlab.live_ops.cli import add_live_ops_parser, run_live_ops_command
from quantlab.monitoring.cli import add_monitor_parser, run_monitor_command
from quantlab.ops.cli import add_ops_parser, run_ops_command
from quantlab.orchestration.cli import (
    add_experiment_parser,
    add_hypothesis_parser,
    run_experiment_command,
    run_hypothesis_command,
)
from quantlab.paper_oms.cli import add_paper_parser, run_paper_command
from quantlab.portfolio.cli import add_portfolio_parser, run_portfolio_command
from quantlab.production_shadow.cli import (
    add_production_shadow_parser,
    run_production_shadow_command,
)
from quantlab.realtime_data.cli import (
    add_market_data_parser,
    add_realtime_parser,
    run_market_data_command,
    run_realtime_command,
)
from quantlab.realtime_decision.cli import (
    add_realtime_decision_parser,
    run_realtime_decision_command,
)
from quantlab.reconciliation.cli import add_reconciliation_parser, run_reconciliation_command
from quantlab.regimes.cli import (
    add_regime_parser,
    add_state_parser,
    run_regime_command,
    run_state_command,
)
from quantlab.release.cli import add_certification_parser, run_certification_command
from quantlab.research.cli import add_research_parsers, run_research_command
from quantlab.research.pipeline import run_momentum_vertical_slice
from quantlab.risk.cli import add_risk_parser, run_risk_command
from quantlab.safety.cli import add_safety_parser, run_safety_command
from quantlab.shadow.cli import add_shadow_parser, run_shadow_command
from quantlab.tca.cli import add_tca_parser, run_tca_command
from quantlab.trade_candidates.cli import add_candidates_parser, run_candidates_command
from quantlab.trade_levels.cli import add_trade_levels_parser, run_trade_levels_command


def main() -> None:
    parser = argparse.ArgumentParser(prog="quantlab")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("slice", help="run the Day-1 momentum vertical slice")
    sub.add_parser("desktop", help="launch the QUANT LAB desktop application")
    add_data_parser(sub)
    add_agents_parser(sub)
    add_candidates_parser(sub)
    add_trade_levels_parser(sub)
    add_feature_parser(sub)
    add_alpha_parser(sub)
    add_portfolio_parser(sub)
    add_factor_parser(sub)
    add_risk_parser(sub)
    add_state_parser(sub)
    add_regime_parser(sub)
    add_adaptive_parser(sub)
    add_model_parser(sub)
    add_ensemble_parser(sub)
    add_execution_parser(sub)
    add_execution_authorization_parser(sub)
    add_hypothesis_parser(sub)
    add_experiment_parser(sub)
    add_discovery_parser(sub)
    add_knowledge_parser(sub)
    add_capital_parser(sub)
    add_paper_parser(sub)
    add_monitor_parser(sub)
    add_ops_parser(sub)
    add_live_ops_parser(sub)
    add_tca_parser(sub)
    add_econometrics_parser(sub)
    add_validation_parser(sub)
    add_certification_parser(sub)
    add_realtime_parser(sub)
    add_market_data_parser(sub)
    add_realtime_decision_parser(sub)
    add_twin_parser(sub)
    add_safety_parser(sub)
    add_shadow_parser(sub)
    add_production_shadow_parser(sub)
    add_broker_parser(sub)
    add_reconciliation_parser(sub)
    add_research_parsers(sub)
    args = parser.parse_args()
    settings = get_settings()
    configure_logging(settings.log_level)
    if args.cmd == "slice":
        result, run = run_momentum_vertical_slice(
            Path(settings.experiment_ledger_path),
            fabric_root=resolve_fabric_root(),
        )
        print(
            json.dumps(
                {
                    "experiment_id": run.id,
                    "hypothesis_id": run.hypothesis_id,
                    "dataset_id": run.dataset_id,
                    "data_kind": run.data_kind,
                    "total_return": result.total_return,
                    "sharpe": result.metrics.get("sharpe"),
                    "max_drawdown": result.max_drawdown,
                    "n_rebalances": result.n_rebalances,
                    "integrity": result.integrity,
                    "live_trading": False,
                },
                indent=2,
            )
        )
    elif args.cmd == "desktop":
        from quantlab.ui.main import main as desktop_main

        raise SystemExit(desktop_main())
    elif args.cmd == "data":
        raise SystemExit(run_data_command(args))
    elif args.cmd == "agents":
        raise SystemExit(run_agents_command(args))
    elif args.cmd == "candidates":
        raise SystemExit(run_candidates_command(args))
    elif args.cmd == "trade-levels":
        raise SystemExit(run_trade_levels_command(args))
    elif args.cmd == "feature":
        raise SystemExit(run_feature_command(args))
    elif args.cmd == "alpha":
        raise SystemExit(run_alpha_command(args))
    elif args.cmd == "portfolio":
        raise SystemExit(run_portfolio_command(args))
    elif args.cmd == "factor":
        raise SystemExit(run_factor_command(args))
    elif args.cmd == "risk":
        raise SystemExit(run_risk_command(args))
    elif args.cmd == "state":
        raise SystemExit(run_state_command(args))
    elif args.cmd == "regime":
        raise SystemExit(run_regime_command(args))
    elif args.cmd == "adaptive":
        raise SystemExit(run_adaptive_command(args))
    elif args.cmd == "model":
        raise SystemExit(run_model_command(args))
    elif args.cmd == "ensemble":
        raise SystemExit(run_ensemble_command(args))
    elif args.cmd == "execution":
        raise SystemExit(run_execution_command(args))
    elif args.cmd == "execution-auth":
        raise SystemExit(run_execution_authorization_command(args))
    elif args.cmd == "hypothesis":
        raise SystemExit(run_hypothesis_command(args))
    elif args.cmd == "experiment":
        raise SystemExit(run_experiment_command(args))
    elif args.cmd == "discovery":
        raise SystemExit(run_discovery_command(args))
    elif args.cmd == "knowledge":
        raise SystemExit(run_knowledge_command(args))
    elif args.cmd == "capital":
        raise SystemExit(run_capital_command(args))
    elif args.cmd == "paper":
        raise SystemExit(run_paper_command(args))
    elif args.cmd == "monitor":
        raise SystemExit(run_monitor_command(args))
    elif args.cmd == "ops":
        raise SystemExit(run_ops_command(args))
    elif args.cmd == "live-ops":
        raise SystemExit(run_live_ops_command(args))
    elif args.cmd == "tca":
        raise SystemExit(run_tca_command(args))
    elif args.cmd == "econometrics":
        raise SystemExit(run_econometrics_command(args))
    elif args.cmd == "validation":
        raise SystemExit(run_validation_command(args))
    elif args.cmd == "certification":
        raise SystemExit(run_certification_command(args))
    elif args.cmd == "realtime":
        raise SystemExit(run_realtime_command(args))
    elif args.cmd == "market-data":
        raise SystemExit(run_market_data_command(args))
    elif args.cmd == "realtime-decision":
        raise SystemExit(run_realtime_decision_command(args))
    elif args.cmd == "twin":
        raise SystemExit(run_twin_command(args))
    elif args.cmd == "broker":
        raise SystemExit(run_broker_command(args))
    elif args.cmd == "reconcile":
        raise SystemExit(run_reconciliation_command(args))
    elif args.cmd == "safety":
        raise SystemExit(run_safety_command(args))
    elif args.cmd == "shadow":
        raise SystemExit(run_shadow_command(args))
    elif args.cmd == "shadow-prod":
        raise SystemExit(run_production_shadow_command(args))
    elif args.cmd in {"backtest", "validate", "research"}:
        raise SystemExit(run_research_command(args))


if __name__ == "__main__":
    main()
