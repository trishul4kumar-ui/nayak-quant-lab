from __future__ import annotations

from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QTableWidget, QVBoxLayout

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.health import ComponentStatus
from quantlab.ui.widgets.charts import DashboardStrip, KpiCard
from quantlab.ui.widgets.data_table import fill_table
from quantlab.ui.widgets.lab_shell import LabPageShell, StatusBadge


class SystemPage(LabPageShell):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "System",
            subtitle=f"Health dashboard for NAYAK QUANT LAB {runtime.version}.",
            nayak_summary=(
                "Green means the lab can run research. Live trading stays blocked "
                "until every safety gate passes — default is closed."
            ),
        )
        self._runtime = runtime
        body = self.body()

        banner = QFrame()
        banner.setObjectName("pulseCard")
        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(14, 12, 14, 12)
        self._banner_title = QLabel()
        self._banner_title.setStyleSheet("font-size: 16px; font-weight: 700;")
        self._banner_detail = QLabel()
        self._banner_detail.setObjectName("nayakVoice")
        self._banner_detail.setWordWrap(True)
        banner_layout.addWidget(self._banner_title)
        banner_layout.addWidget(self._banner_detail)
        body.addWidget(banner)

        self._dash = DashboardStrip(["Components OK", "Gates passing", "Live status", "Version"])
        body.addWidget(self._dash)

        self._badge_row = StatusBadge("ready", text="RESEARCH MODE")
        body.addWidget(self._badge_row)

        grid_label = QLabel("Component health")
        grid_label.setStyleSheet("font-weight: 600; font-size: 13px;")
        body.addWidget(grid_label)
        self._health_grid = QFrame()
        self._health_grid.setObjectName("dashboardStrip")
        self._grid_layout = QGridLayout(self._health_grid)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(8)
        self._health_cards: list[KpiCard] = []
        body.addWidget(self._health_grid)

        self.table = QTableWidget()
        self.gates = QTableWidget()
        body.addWidget(self.table, 2)
        gates_label = QLabel("Live safety gates")
        gates_label.setStyleSheet("font-weight: 600; font-size: 13px;")
        body.addWidget(gates_label)
        body.addWidget(self.gates, 1)
        self.refresh()

    def refresh(self) -> None:
        runtime = self._runtime
        status = runtime.refresh_status()
        components = runtime.health.components
        ok_count = sum(1 for c in components if c.status is ComponentStatus.OK)
        gate_pass = sum(
            1
            for name in (
                "live_trading",
                "live_trading_enabled",
                "broker_connected",
                "risk_engine_healthy",
                "strategy_approved",
                "model_approved",
                "data_healthy",
                "session_valid",
            )
            if bool(getattr(runtime.gates, name))
        )
        if runtime.gates.all_pass():
            self._badge_row.setText("LIVE GATES PASSING")
            banner_tone = "All live safety gates pass — research and paper paths only unless armed."
        elif "LIVE" in status.live_trading.upper() and "DISABLE" not in status.live_trading.upper():
            self._badge_row.setText("LIVE ARMED")
            banner_tone = "Live path is armed. Double-check broker and risk before any order."
        else:
            self._badge_row.setText("RESEARCH MODE")
            banner_tone = "Default closed: synthetic research mode. Live trading blocked."
        self._banner_title.setText(f"System · {status.live_trading}")
        self._banner_detail.setText(
            f"{banner_tone} {ok_count}/{len(components)} components healthy · "
            f"{gate_pass}/8 gates true."
        )
        self._dash.card(0).set_value(f"{ok_count}/{len(components)}", accent="#66bb6a")
        self._dash.card(1).set_value(f"{gate_pass}/8")
        self._dash.card(2).set_value(status.live_trading[:14])
        self._dash.card(3).set_value(runtime.version)

        while self._health_cards:
            card = self._health_cards.pop()
            self._grid_layout.removeWidget(card)
            card.deleteLater()
        for i, component in enumerate(components[:8]):
            mark = {
                ComponentStatus.OK: "OK",
                ComponentStatus.OPTIONAL: "OPT",
                ComponentStatus.FAILED: "FAIL",
            }[component.status]
            accent = {
                ComponentStatus.OK: "#66bb6a",
                ComponentStatus.OPTIONAL: "#ffa726",
                ComponentStatus.FAILED: "#ef5350",
            }[component.status]
            card = KpiCard(component.name[:14], mark, accent=accent, subtitle=component.detail[:40])
            self._health_cards.append(card)
            self._grid_layout.addWidget(card, i // 4, i % 4)

        rows = []
        for component in components:
            mark = {
                ComponentStatus.OK: "OK",
                ComponentStatus.OPTIONAL: "OPTIONAL",
                ComponentStatus.FAILED: "FAILED",
            }[component.status]
            rows.append([component.name, mark, component.detail])
        fill_table(self.table, ["Component", "Status", "Detail"], rows, badge_columns={1})
        gate_rows = [
            [name.replace("_", " "), str(getattr(runtime.gates, name))]
            for name in (
                "live_trading",
                "live_trading_enabled",
                "broker_connected",
                "risk_engine_healthy",
                "strategy_approved",
                "model_approved",
                "data_healthy",
                "session_valid",
            )
        ]
        fill_table(self.gates, ["Gate", "Value"], gate_rows, badge_columns={1})
