"""Application runtime. No PySide6 imports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quantlab import __version__
from quantlab.app.chart_history import ChartDataSession
from quantlab.app.commands import request_live_trading
from quantlab.app.health import HealthReport, run_health_checks
from quantlab.app.jobs import Job, JobService
from quantlab.app.live_market import LiveMarketFeed
from quantlab.app.log_buffer import LogBuffer
from quantlab.app.mode import AppMode, resolve_mode
from quantlab.app.paths import RuntimePaths
from quantlab.app.settings_store import UiSettingsStore
from quantlab.app.status import SystemStatus
from quantlab.app.worker import run_backtest_spawned, run_validation_spawned
from quantlab.core.config import LiveSafetyGates, Settings, get_settings
from quantlab.core.errors import SafetyError
from quantlab.core.logging import configure_logging
from quantlab.data.fabric.layout import FabricLayout
from quantlab.models.registry import ExperimentLedger
from quantlab.restricted_execution.repository import configure_durable_store
from quantlab.risk.states import RiskState


class ApplicationRuntime:
    def __init__(
        self,
        *,
        settings: Settings,
        paths: RuntimePaths,
        mode: AppMode,
        gates: LiveSafetyGates,
        jobs: JobService,
        logs: LogBuffer,
        ledger: ExperimentLedger,
        ui_settings: UiSettingsStore,
        health: HealthReport,
        status: SystemStatus,
        risk_state: RiskState = RiskState.NORMAL,
    ) -> None:
        self.version = __version__
        self.settings = settings
        self.paths = paths
        self.mode = mode
        self.gates = gates
        self.jobs = jobs
        self.logs = logs
        self.ledger = ledger
        self.ui_settings = ui_settings
        self.health = health
        self.status = status
        self.risk_state = risk_state
        self.notifications: list[str] = []
        self._closed = False
        self.workspace_revision = 0
        self.jobs.set_event_sink(self.logs.append)
        self.live_market = LiveMarketFeed()
        self.chart_data = ChartDataSession()

    @property
    def is_closed(self) -> bool:
        return self._closed

    def submit_momentum_backtest(self, parameters: dict[str, Any] | None = None) -> Job:
        from quantlab.data.policy import fixtures_enabled

        if not fixtures_enabled() and not self.settings.research_dataset:
            raise SafetyError(
                "REAL_VALIDATED_DATASET_REQUIRED: cross-sectional momentum requires a "
                "verified REAL PIT dataset. Use Backtest Lab for the broker-history SMA baseline."
            )
        params = dict(parameters or {})
        params.setdefault("fabric_root", str(self.paths.fabric_dir))
        self.logs.append(
            {
                "event": "backtest_submitted",
                "component": "app",
                "level": "info",
                "parameters": params,
            }
        )

        def _run(job: Job) -> dict[str, Any]:
            return run_backtest_spawned(job, self.paths.ledger_path)

        return self.jobs.submit("backtest", _run, params)

    def submit_momentum_validation(self, parameters: dict[str, Any] | None = None) -> Job:
        from quantlab.data.policy import fixtures_enabled

        if not fixtures_enabled() and not self.settings.research_dataset:
            raise SafetyError(
                "REAL_VALIDATION_INPUTS_REQUIRED: the legacy suite generates fixture prices. "
                "Supply an independently verified REAL PIT dataset and strategy protocol; "
                "a broker-history baseline cannot substitute validation."
            )
        params = dict(parameters or {})
        params.setdefault("fabric_root", str(self.paths.fabric_dir))
        self.logs.append(
            {
                "event": "validation_submitted",
                "component": "app",
                "level": "info",
                "parameters": params,
            }
        )

        def _run(job: Job) -> dict[str, Any]:
            return run_validation_spawned(job, self.paths.ledger_path, self.paths.artifacts_dir)

        return self.jobs.submit("validate", _run, params)

    def submit_market_backtest(self, parameters: dict[str, Any]) -> Job:
        """One GET-only, frozen real-history research job; never orders or synthetic fallback."""
        from quantlab.app.market_backtest import MarketBacktestParameters, execute_market_backtest

        if self.is_closed or self.gates.live_trading or self.gates.broker_write_enabled:
            raise SafetyError("RESEARCH_ONLY_RUNTIME_REQUIRED")
        validated = MarketBacktestParameters.model_validate(parameters)

        def work(job: Job) -> dict[str, Any]:
            return execute_market_backtest(
                job,
                self.paths.ledger_path,
                self.paths.artifacts_dir,
                self.paths.database_dir / "agent_desk.sqlite",
                fabric_root=self.paths.fabric_dir,
            )

        return self.jobs.submit("market_backtest", work, validated.model_dump(mode="json"))

    def submit_history_capture(self, parameters: dict[str, Any]) -> Job:
        from quantlab.app.market_backtest import MarketBacktestParameters
        from quantlab.app.real_history import execute_history_capture

        if self.is_closed or self.gates.live_trading or self.gates.broker_write_enabled:
            raise SafetyError("RESEARCH_ONLY_RUNTIME_REQUIRED")
        validated = MarketBacktestParameters.model_validate(parameters)

        def work(job: Job) -> dict[str, Any]:
            return execute_history_capture(
                job, self.paths.database_dir / "agent_desk.sqlite", self.paths.fabric_dir
            )

        return self.jobs.submit("history_capture", work, validated.model_dump(mode="json"))

    @property
    def artifact_repository_path(self) -> Path:
        return self.paths.database_dir / "agent_desk.sqlite"

    def _assert_research_runtime(self) -> None:
        if self.is_closed or self.gates.live_trading or self.gates.broker_write_enabled:
            raise SafetyError("RESEARCH_ONLY_RUNTIME_REQUIRED")

    def submit_research_workbench(self, parameters: dict[str, Any]) -> Job:
        """Run an explicit engine against exact frozen REAL input artifacts."""
        from quantlab.app.research_workbench import (
            ResearchRunParameters,
            execute_research_workbench,
        )

        self._assert_research_runtime()
        validated = ResearchRunParameters.model_validate(parameters)

        def work(job: Job) -> dict[str, Any]:
            return execute_research_workbench(
                job,
                self.artifact_repository_path,
                self.paths.ledger_path,
                self.paths.fabric_dir,
            )

        return self.jobs.submit(
            "research_" + validated.engine, work, validated.model_dump(mode="json")
        )

    def submit_paper_workflow(self, parameters: dict[str, Any]) -> Job:
        """Explicit sourced paper accounting; never a broker order capability."""
        from quantlab.app.paper_workflow import execute_paper_workflow

        self._assert_research_runtime()
        kind = str(parameters.get("kind", ""))
        if kind not in {"prepare", "capital", "paper_oms", "monitoring", "tca", "shadow", "twin"}:
            raise ValueError("PAPER_WORKFLOW_KIND_REQUIRED")

        def work(job: Job) -> dict[str, Any]:
            return execute_paper_workflow(
                job,
                repository_path=self.artifact_repository_path,
                ledger_path=self.paths.ledger_path,
                fabric_root=self.paths.fabric_dir,
            )

        return self.jobs.submit("paper_" + kind, work, dict(parameters))

    def submit_history_batch(self, parameters: dict[str, Any]) -> Job:
        from quantlab.app.history_batch import HistoryCaptureBatch, execute_history_batch

        self._assert_research_runtime()
        validated = HistoryCaptureBatch.model_validate(parameters)

        def work(job: Job) -> dict[str, Any]:
            return execute_history_batch(job, self.artifact_repository_path, self.paths.fabric_dir)

        return self.jobs.submit("history_batch", work, validated.model_dump(mode="json"))

    def submit_strategy_research(self, parameters: dict[str, Any], *, provider: Any = None) -> Job:
        """One user-started automatic, finite strategy research batch; never orders."""
        from quantlab.app.strategy_research import (
            StrategyBatchParameters,
            execute_strategy_research,
        )

        self._assert_research_runtime()
        validated = StrategyBatchParameters.model_validate(parameters)

        def work(job: Job) -> dict[str, Any]:
            return execute_strategy_research(
                job,
                self.artifact_repository_path,
                self.paths.ledger_path,
                self.paths.fabric_dir,
                provider=provider,
            )

        return self.jobs.submit("ai_strategy_research", work, validated.model_dump(mode="json"))

    def reject_workflow(self, workflow: str, reason: str) -> None:
        """Record bounded local preflight diagnostics, never raw request parameters."""
        from quantlab.agents.hashing import safe_text

        self.logs.append(
            {
                "event": "workflow_rejected",
                "component": "workbench",
                "level": "warning",
                "workflow": workflow[:60],
                "reason": safe_text(reason)[:500],
            }
        )

    def try_enable_live(self) -> None:
        request_live_trading(self.gates)

    def refresh_status(self) -> SystemStatus:
        self.status = SystemStatus.from_health(self.health, self.gates, self.risk_state)
        return self.status

    def record_notification(self, message: str) -> None:
        self.notifications.append(message)
        self.logs.append({"event": "notification", "component": "app", "message": message})

    def shutdown(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.live_market.close()
        self.chart_data.close()
        self.jobs.shutdown(wait=True)
        self.ui_settings.save()
        self.logs.flush()
        self.logs.append({"event": "shutdown", "component": "app", "level": "info"})


def bootstrap(*, data_dir: Path | None = None) -> ApplicationRuntime:
    get_settings.cache_clear()
    settings = Settings()
    override = data_dir if data_dir is not None else settings.data_dir
    paths = RuntimePaths.discover(override)
    paths.ensure()
    FabricLayout(paths.fabric_dir).ensure()
    configure_durable_store(paths.database_dir / "control_plane.sqlite")
    logs = LogBuffer(log_file=paths.log_file)
    configure_logging(settings.log_level, sink=logs.append)
    gates = LiveSafetyGates()
    mode = resolve_mode(settings.quant_lab_mode, gates)
    jobs = JobService(paths.db_path)
    ledger = ExperimentLedger(paths.ledger_path)
    ui_settings = UiSettingsStore(paths.settings_path)
    health = run_health_checks(paths, settings, gates, mode)
    status = SystemStatus.from_health(health, gates)
    logs.append(
        {
            "event": "bootstrap",
            "component": "app",
            "level": "info",
            "mode": mode.value,
            "live_trading": gates.live_trading,
            "version": __version__,
        }
    )
    return ApplicationRuntime(
        settings=settings,
        paths=paths,
        mode=mode,
        gates=gates,
        jobs=jobs,
        logs=logs,
        ledger=ledger,
        ui_settings=ui_settings,
        health=health,
        status=status,
    )
