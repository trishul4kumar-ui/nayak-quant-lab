from __future__ import annotations

from PySide6.QtWidgets import QLabel

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.monitoring import last_run_row, run_payload
from quantlab.ui.widgets.catalog_page import CatalogLabPage


class MonitoringLabPage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Monitoring Lab",
            subtitle="Post-decision performance, attribution, drift, and feedback.",
            nayak_summary=(
                "Monitoring explains what happened after a paper book was marked. "
                "A profitable observation is not automatically alpha."
            ),
            technical=(
                "This page queries quantlab.app.monitoring. "
                "Qt does not parse Parquet, query DuckDB, compute attribution, "
                "mutate decisions, or place orders."
            ),
            catalog_title="Last monitoring diagnostics",
            catalog_headers=["Field", "Value", "Kind", "Note"],
            last_title="Last monitoring run",
            empty_title="No monitoring run yet",
            empty_body="RUN MONITOR attributes the last paper OMS book. LIVE remains disabled.",
            empty_action="RUN MONITOR",
            on_empty_action=self._run_monitor,
        )
        self._runtime = runtime
        badges = QLabel("PAPER  ·  LIVE DISABLED  ·  performance is not a claim")
        badges.setWordWrap(True)
        self.body().addWidget(badges)
        self.refresh()

    def _run_monitor(self) -> None:
        run_payload()
        self.refresh()

    def refresh(self) -> None:
        last = last_run_row()
        if last is None:
            self.set_catalog_rows([])
            self.set_last_run(None)
            return
        self.set_catalog_rows(
            [
                ["P&L", str(last["pnl"]), "absolute", "not alpha"],
                ["Residual", str(last["residual"]), "identity", "visible"],
                ["Drift", str(last["drift"]), "target vs book", "no rebalance"],
                ["Hash", str(last["hash"]), "identity", "deterministic"],
            ]
        )
        self.set_last_run(
            [
                ("Monitoring run", str(last["id"])),
                ("P&L", str(last["pnl"])),
                ("Residual", str(last["residual"])),
                ("Drift", str(last["drift"])),
                ("Hash", str(last["hash"])),
                ("Note", "PAPER. Not LIVE. Profit is not a claim."),
            ]
        )
