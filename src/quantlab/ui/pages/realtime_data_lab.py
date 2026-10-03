from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPushButton

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.realtime_data import (
    capture_kite_snapshot_payload,
    connect_kite_payload,
    last_run_row,
    run_payload,
)
from quantlab.realtime_data.kite import KiteMarketDataAdapter
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
        self._kite_state = QLabel("Kite feed not configured")
        self.add_toolbar_widget(self._kite_state)
        self._kite_connect = QPushButton("Connect Kite")
        self._kite_connect.setToolTip(
            "Configure a read-only Kite quote source for this desktop session"
        )
        self._kite_connect.clicked.connect(self._connect_kite)
        self.add_toolbar_widget(self._kite_connect)
        self._kite_capture = QPushButton("Capture Kite snapshot")
        self._kite_capture.setObjectName("primary")
        self._kite_capture.setToolTip("Fetch one live quote snapshot; no order path exists")
        self._kite_capture.setEnabled(False)
        self._kite_capture.clicked.connect(self._capture_kite)
        self.add_toolbar_widget(self._kite_capture)
        badges = QLabel("LIVE DISABLED  ·  OBSERVE-ONLY  ·  NO ORDER ROUTING")
        badges.setWordWrap(True)
        self.body().addWidget(badges)
        self.refresh()

    def _run(self) -> None:
        run_payload()
        self.refresh()

    def _connect_kite(self) -> None:
        result = connect_kite_payload()
        if "error" in result:
            self._kite_state.setText("Kite unavailable")
            self._kite_state.setToolTip(str(result["error"]))
            self._kite_capture.setEnabled(False)
            return
        self._kite_state.setText("Kite read-only connected")
        self._kite_state.setToolTip(
            "Configured for quote observation only; live trading remains disabled"
        )
        self._kite_capture.setEnabled(True)

    def _capture_kite(self) -> None:
        result = capture_kite_snapshot_payload()
        if "error" in result:
            self._kite_state.setText("Kite quote failed")
            self._kite_state.setToolTip(str(result["error"]))
            return
        self._kite_state.setText("Kite snapshot captured")
        self._kite_state.setToolTip("Frozen read-only quote state; inspect quality before use")
        self.refresh()

    def refresh(self) -> None:
        configured = KiteMarketDataAdapter.environment_configured()
        self._kite_connect.setEnabled(configured)
        self._kite_capture.setEnabled(configured and self._kite_capture.isEnabled())
        if not configured:
            self._kite_state.setText("Kite feed not configured")
            self._kite_state.setToolTip(
                "Set KITE_API_KEY, KITE_ACCESS_TOKEN, and KITE_MARKET_DATA_SYMBOLS in .env"
            )
            self._kite_connect.setToolTip(
                "Add read-only Kite credentials and explicit symbols to .env, then restart the lab"
            )
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
