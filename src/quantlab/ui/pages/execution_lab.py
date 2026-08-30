from __future__ import annotations

from PySide6.QtWidgets import QLabel, QTableWidget

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.live_ops import execution_monitor_rows
from quantlab.app.queries import execution_catalog_rows, last_execution_experiment_row
from quantlab.ui.widgets.catalog_page import CatalogLabPage
from quantlab.ui.widgets.data_table import fill_table


class ExecutionLabPage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Execution Lab",
            subtitle="Simulate spreads, slippage, and impact — not broker fills.",
            nayak_summary=(
                "Execution research asks how costs erode returns. "
                "Simulated fills are not real orders; "
                "synthetic volume is not NSE average daily volume."
            ),
            technical=(
                "Microstructure models run offline; "
                "live order routing stays blocked in research mode."
            ),
            catalog_title="Seed execution models",
            catalog_headers=["Model", "Spread", "Slippage", "Impact", "Latency"],
            last_title="Last execution experiment",
            dashboard_titles=["Net return", "Model", "Gate", "Data"],
        )
        self._runtime = runtime
        monitor_label = QLabel("Order / fill monitor")
        monitor_label.setObjectName("sectionTitle")
        monitor_label.setStyleSheet("font-weight: 600; font-size: 13px;")
        self._monitor_note = QLabel()
        self._monitor_note.setWordWrap(True)
        self._monitor_note.setObjectName("nayakVoice")
        self._monitor = QTableWidget()
        self.insert_before_last_run(self._monitor, label=monitor_label)
        body = self.body()
        idx = body.indexOf(self._monitor)
        body.insertWidget(idx, self._monitor_note)
        self.refresh()

    def refresh(self) -> None:
        self.set_catalog_rows(
            [
                [
                    str(row["definition_id"]),
                    str(row["spread_model"]),
                    str(row["slippage_model"]),
                    str(row["impact_model"]),
                    str(row["latency_sessions"]),
                ]
                for row in execution_catalog_rows()
            ]
        )
        rows, note = execution_monitor_rows(self._runtime)
        self._monitor_note.setText(note)
        if rows:
            fill_table(self._monitor, ["Id", "Model", "Status", "Detail"], rows)
            self._monitor.setVisible(True)
        else:
            self._monitor.setVisible(False)

        last = last_execution_experiment_row(self._runtime)
        dash = self.dashboard
        if last is None:
            self.set_last_run(None)
            if dash is not None:
                for card in dash.cards:
                    card.set_value("—")
            return
        net = last.get("net_return")
        if dash is not None:
            dash.card(0).set_value("" if net is None else str(net))
            dash.card(1).set_value(str(last.get("execution_model_id", "—"))[:14])
            dash.card(2).set_value(str(last.get("gate_outcome", "—"))[:12])
            dash.card(3).set_value(str(last.get("data_kind", "—"))[:12])
        self.set_last_run(
            [
                ("experiment", str(last["id"])[:16]),
                ("model", str(last["execution_model_id"])),
                ("scenario", str(last["scenario_id"])),
                ("gate", str(last["gate_outcome"])),
                ("data", str(last["data_kind"])),
                ("net_return", "" if last["net_return"] is None else str(last["net_return"])),
            ]
        )
