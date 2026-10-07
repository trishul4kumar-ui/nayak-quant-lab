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
        self.live_market = LiveMarketFeed()
        self.chart_data = ChartDataSession()

    @property
    def is_closed(self) -> bool:
        return self._closed

    def submit_momentum_backtest(self, parameters: dict[str, Any] | None = None) -> Job:
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
