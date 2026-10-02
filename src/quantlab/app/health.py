"""Startup health. Broker/AI are optional in research mode."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from quantlab.app.mode import AppMode
from quantlab.app.paths import RuntimePaths
from quantlab.core.config import LiveSafetyGates, Settings


class ComponentStatus(StrEnum):
    OK = "ok"
    OPTIONAL = "optional"
    FAILED = "failed"


class ComponentHealth(BaseModel):
    name: str
    status: ComponentStatus
    detail: str
    required: bool = True


class HealthReport(BaseModel):
    mode: AppMode
    live_trading: bool
    components: list[ComponentHealth] = Field(default_factory=list)

    def research_ready(self) -> bool:
        return all(c.status is not ComponentStatus.FAILED for c in self.components if c.required)

    def by_name(self, name: str) -> ComponentHealth | None:
        for component in self.components:
            if component.name == name:
                return component
        return None


def run_health_checks(
    paths: RuntimePaths,
    settings: Settings,
    gates: LiveSafetyGates,
    mode: AppMode,
) -> HealthReport:
    components: list[ComponentHealth] = []

    try:
        import quantlab

        components.append(
            ComponentHealth(
                name="core_engine",
                status=ComponentStatus.OK,
                detail=f"quantlab {quantlab.__version__}",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="core_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        import sqlite3

        conn = sqlite3.connect(str(paths.db_path))
        conn.execute("SELECT 1")
        conn.close()
        components.append(
            ComponentHealth(
                name="database",
                status=ComponentStatus.OK,
                detail=str(paths.db_path),
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="database",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    writable = os_access_write(paths.root)
    components.append(
        ComponentHealth(
            name="data_store",
            status=ComponentStatus.OK if writable else ComponentStatus.FAILED,
            detail=str(paths.root),
        )
    )

    try:
        import duckdb
        import pyarrow

        from quantlab.data.fabric.layout import FabricLayout

        layout = FabricLayout(paths.fabric_dir)
        layout.ensure()
        components.append(
            ComponentHealth(
                name="data_fabric",
                status=ComponentStatus.OK,
                detail=(f"duckdb={duckdb.__version__} pyarrow={pyarrow.__version__} {layout.root}"),
                required=True,
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="data_fabric",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    components.append(
        ComponentHealth(
            name="configuration",
            status=ComponentStatus.OK,
            detail=f"mode={mode.value} env={settings.quant_lab_env}",
        )
    )

    try:
        from quantlab.research.pipeline import run_momentum_vertical_slice

        assert run_momentum_vertical_slice is not None
        components.append(
            ComponentHealth(
                name="research_engine",
                status=ComponentStatus.OK,
                detail="momentum slice available",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="research_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.features.registry import get_feature

        get_feature("momentum_20")
        components.append(
            ComponentHealth(
                name="feature_engine",
                status=ComponentStatus.OK,
                detail="seed library loaded",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="feature_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.backtest.engine import run_backtest

        assert run_backtest is not None
        components.append(
            ComponentHealth(
                name="backtest_engine",
                status=ComponentStatus.OK,
                detail="next-bar engine",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="backtest_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.portfolio.builder import construct_targets
        from quantlab.portfolio.spec import list_portfolio_models

        assert construct_targets is not None
        n_models = len(list_portfolio_models())
        components.append(
            ComponentHealth(
                name="portfolio_engine",
                status=ComponentStatus.OK,
                detail=f"{n_models} seed constructors; target weights are not orders",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="portfolio_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.factors.registry import get_factor, list_factors

        get_factor("market_ew_beta")
        n_factors = len(list_factors())
        components.append(
            ComponentHealth(
                name="factor_engine",
                status=ComponentStatus.OK,
                detail=f"{n_factors} seed factors; unsupported stay NOT_TESTED",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="factor_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.risk.model import list_risk_models

        n_models = len(list_risk_models())
        components.append(
            ComponentHealth(
                name="research_risk_model",
                status=ComponentStatus.OK,
                detail=f"{n_models} research covariance specs; not the live firewall",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="research_risk_model",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.regimes.registry import get_regime_model, list_regime_models

        get_regime_model("vol_tercile")
        n_models = len(list_regime_models())
        components.append(
            ComponentHealth(
                name="regime_engine",
                status=ComponentStatus.OK,
                detail=f"{n_models} seed detectors; HMM smoothing blocked for prediction",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="regime_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.adaptive.registry import get_adaptive_model, list_adaptive_models

        get_adaptive_model("static_mom20")
        n_models = len(list_adaptive_models())
        components.append(
            ComponentHealth(
                name="adaptive_engine",
                status=ComponentStatus.OK,
                detail=f"{n_models} seed learners; predict-then-update; not a live agent",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="adaptive_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.learning.registry import get_model, list_models

        get_model("ols_mom")
        n_stat = len(list_models())
        components.append(
            ComponentHealth(
                name="learning_engine",
                status=ComponentStatus.OK,
                detail=f"{n_stat} seed models; walk-forward; not AutoML",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="learning_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.ensemble.registry import get_ensemble, list_ensembles

        get_ensemble("ew_mom_5_20")
        n_ens = len(list_ensembles())
        components.append(
            ComponentHealth(
                name="ensemble_engine",
                status=ComponentStatus.OK,
                detail=f"{n_ens} seed combinations; PIT combine; not a second portfolio engine",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="ensemble_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.execution_research.registry import get_execution_model, list_execution_models

        get_execution_model("exec_base")
        n_exec = len(list_execution_models())
        components.append(
            ComponentHealth(
                name="execution_research_engine",
                status=ComponentStatus.OK,
                detail=f"{n_exec} seed microstructure models; simulated fills; not OMS live",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="execution_research_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.orchestration.registry import get_hypothesis, list_hypotheses

        get_hypothesis("H-MOM-001")
        n_hyp = len(list_hypotheses())
        components.append(
            ComponentHealth(
                name="orchestration_engine",
                status=ComponentStatus.OK,
                detail=f"{n_hyp} seed hypotheses; control plane; not a second gate",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="orchestration_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.discovery.registry import list_families

        n_fam = len(list_families())
        components.append(
            ComponentHealth(
                name="discovery_engine",
                status=ComponentStatus.OK,
                detail=f"{n_fam} discovery families; hypotheses only; not a second gate",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="discovery_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.knowledge.memory import seed_graph

        graph = seed_graph()
        components.append(
            ComponentHealth(
                name="knowledge_engine",
                status=ComponentStatus.OK,
                detail=(f"{len(graph.nodes)} seed nodes; memory not authority; not a second gate"),
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="knowledge_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.capital.library import list_policies

        n_pol = len(list_policies())
        components.append(
            ComponentHealth(
                name="capital_engine",
                status=ComponentStatus.OK,
                detail=(
                    f"{n_pol} capital policies; targets not orders; not a second portfolio engine"
                ),
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="capital_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.paper_oms.policy import list_policies as list_paper_policies

        n_pol = len(list_paper_policies())
        components.append(
            ComponentHealth(
                name="paper_oms_engine",
                status=ComponentStatus.OK,
                detail=(
                    f"{n_pol} paper execution policies; simulated fills only; live path closed"
                ),
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="paper_oms_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.monitoring.service import run_monitoring

        assert run_monitoring is not None
        components.append(
            ComponentHealth(
                name="monitoring_engine",
                status=ComponentStatus.OK,
                detail="portfolio monitoring/attribution; not a second backtester",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="monitoring_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.data.market_data import get as market_data_get

        assert market_data_get is not None
        components.append(
            ComponentHealth(
                name="market_data_engine",
                status=ComponentStatus.OK,
                detail=(
                    "PIT market data, security master, corporate actions; no invented NSE history"
                ),
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="market_data_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.tca.service import run_tca

        assert run_tca is not None
        components.append(
            ComponentHealth(
                name="tca_engine",
                status=ComponentStatus.OK,
                detail="TCA/calibration/capacity; Prompt 13 models reused; not live",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="tca_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.econometrics.service import run_econometrics

        assert run_econometrics is not None
        components.append(
            ComponentHealth(
                name="econometrics_engine",
                status=ComponentStatus.OK,
                detail="time-series/causal research; Granger is predictive; not a claim",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="econometrics_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.certification.service import run_certification

        assert run_certification is not None
        components.append(
            ComponentHealth(
                name="certification_engine",
                status=ComponentStatus.OK,
                detail="model-risk validation/certification; CERTIFIED is not live",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="certification_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.shadow.service import run_shadow_cycle

        assert run_shadow_cycle is not None
        components.append(
            ComponentHealth(
                name="shadow_engine",
                status=ComponentStatus.OK,
                detail="production paper/shadow; LIVE_TRADING=false; no broker routing",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="shadow_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.safety.service import evaluate_release

        assert evaluate_release is not None
        components.append(
            ComponentHealth(
                name="safety_engine",
                status=ComponentStatus.OK,
                detail="live-trading safety gateway; LIVE_TRADING=false; G15 BLOCK",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="safety_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.ops.service import doctor

        assert doctor is not None
        components.append(
            ComponentHealth(
                name="ops_engine",
                status=ComponentStatus.OK,
                detail="operational control plane; LIVE_TRADING=false; no broker routing",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="ops_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.release.service import evaluate_release_gate

        assert evaluate_release_gate is not None
        components.append(
            ComponentHealth(
                name="release_engine",
                status=ComponentStatus.OK,
                detail="live-certification release gate; CERTIFIED≠LIVE; LIVE_TRADING=false",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="release_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.realtime_data.service import evaluate_realtime_snapshot

        assert evaluate_realtime_snapshot is not None
        components.append(
            ComponentHealth(
                name="realtime_data_engine",
                status=ComponentStatus.OK,
                detail="observe-only market-data gateway; LIVE_TRADING=false; no broker",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="realtime_data_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.realtime_decision.service import run_realtime_decision

        assert run_realtime_decision is not None
        components.append(
            ComponentHealth(
                name="realtime_decision_engine",
                status=ComponentStatus.OK,
                detail="research-to-decision engine; DECISION≠ORDER; LIVE_TRADING=false",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="realtime_decision_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.digital_twin.service import run_twin

        assert run_twin is not None
        components.append(
            ComponentHealth(
                name="digital_twin_engine",
                status=ComponentStatus.OK,
                detail="deterministic shadow/replay twin; ZERO BROKER WRITE; LIVE_TRADING=false",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="digital_twin_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.risk.firewall import RiskFirewall
        from quantlab.risk.states import RiskState

        firewall = RiskFirewall()
        components.append(
            ComponentHealth(
                name="risk_engine",
                status=ComponentStatus.OK,
                detail=f"state={firewall.state.value} halt_blocks={RiskState.HALT.value}",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="risk_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    try:
        from quantlab.execution.engine import ExecutionEngine

        ExecutionEngine(gates)
        components.append(
            ComponentHealth(
                name="execution_engine",
                status=ComponentStatus.OK,
                detail="live path blocked unless gates pass",
            )
        )
    except Exception as exc:
        components.append(
            ComponentHealth(
                name="execution_engine",
                status=ComponentStatus.FAILED,
                detail=str(exc),
            )
        )

    broker_required = mode is AppMode.LIVE
    components.append(
        ComponentHealth(
            name="broker_gateway",
            status=ComponentStatus.FAILED if broker_required else ComponentStatus.OPTIONAL,
            detail="read-only mock available; live vendor adapters disabled",
            required=broker_required,
        )
    )

    components.append(
        ComponentHealth(
            name="ai_services",
            status=ComponentStatus.OPTIONAL,
            detail="permissions only; REQUEST_LIVE_ORDER and OVERRIDE_RESEARCH_GATE denied",
            required=False,
        )
    )

    return HealthReport(mode=mode, live_trading=gates.live_trading, components=components)


def os_access_write(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False
