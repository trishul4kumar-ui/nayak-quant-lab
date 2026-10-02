from __future__ import annotations

from PySide6.QtWidgets import QLabel

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.realtime_data import last_run_row, run_payload
from quantlab.ui.widgets.catalog_page import CatalogLabPage


class RealTimeDataLabPage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Real-Time Data Lab",
            subtitle="Observe-only market state. Not a signal. Not an order.",
            nayak_summary=(
                "What is the frozen MarketState at T, and is the feed healthy enough "
                "to observe — without treating observation as trading?"
            ),
            technical=(
                "This page queries quantlab.app.realtime_data. "
                "Qt does not parse streams, mutate snapshots, touch broker credentials, "
                "or execute. RUN SNAPSHOT is local mock only."
            ),
            catalog_title="Realtime diagnostics",
            catalog_headers=["Field", "Value", "Kind", "Note"],
            last_title="Last frozen snapshot",
            empty_title="No realtime snapshot yet",
            empty_body="RUN SNAPSHOT freezes MarketState(T). LIVE remains disabled.",
            empty_action="RUN SNAPSHOT",
            on_empty_action=self._run,
        )
        self._runtime = runtime
        badges = QLabel("LIVE DISABLED  ·  OBSERVE-ONLY  ·  NO ORDER ROUTING")
        badges.setWordWrap(True)
        self.body().addWidget(badges)
        self.refresh()

    def _run(self) -> None:
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
                ["Quality", str(last["quality"]), "data", "not silently valid"],
                ["Freshness", str(last["freshness"]), "clock", "FRESH ≠ VALID"],
                ["Session", str(last["session"]), "calendar", "weekday IST"],
                [
                    "Source",
                    str(last.get("active_source", "mock-observe-only")),
                    "provenance",
                    "explicit",
                ],
                ["Coverage", str(last.get("coverage", "unknown")), "health", "not inferred"],
                ["Hash", str(last["hash"]), "identity", "immutable"],
            ]
        )
        self.set_last_run(
            [
                ("Snapshot", str(last["id"])),
                ("Quality", str(last["quality"])),
                ("Hash", str(last["hash"])),
                (
                    "Note",
                    "NOT LIVE. REAL-TIME OBSERVATION ≠ TRADING. CONNECTED ≠ HEALTHY.",
                ),
            ]
        )
