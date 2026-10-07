from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel, QPushButton

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.realtime_data import (
    last_run_row,
    record_snapshot_payload,
    run_payload,
)
from quantlab.core.errors import QuantLabError
from quantlab.ui.widgets.catalog_page import CatalogLabPage
from quantlab.ui.widgets.data_table import update_table_values


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
                "or execute. Synthetic demo is explicit; "
                "Kite quotes use a shared background worker."
            ),
            catalog_title="Realtime diagnostics",
            catalog_headers=["Field", "Value", "Kind", "Note"],
            last_title="Last frozen snapshot",
            empty_title="No realtime snapshot yet",
            empty_body="Connect Kite for real quotes, or explicitly run the synthetic demo.",
            empty_action="Run synthetic demo",
            on_empty_action=self._run,
        )
        self._runtime = runtime
        self._capture_after_revision: int | None = None
        self._kite_state = QLabel("Kite · DISCONNECTED")
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
        self._kite_capture.clicked.connect(self._capture_kite)
        self.add_toolbar_widget(self._kite_capture)
        badges = QLabel("LIVE DISABLED  ·  OBSERVE-ONLY  ·  NO ORDER ROUTING")
        badges.setWordWrap(True)
        self.body().addWidget(badges)
        self._kite_error = QLabel()
        self._kite_error.setWordWrap(True)
        self.body().addWidget(self._kite_error)
        self.refresh()
        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._poll)
        self._timer.start()

    def _run(self) -> None:
        run_payload()
        self.refresh()

    def _connect_kite(self) -> None:
        self._runtime.live_market.start()
        self.refresh()

    def _capture_kite(self) -> None:
        feed = self._runtime.live_market
        self._capture_after_revision = feed.revision
        feed.refresh_now()
        self.refresh()

    def _poll(self) -> None:
        if self._runtime.is_closed:
            self._timer.stop()
            return
        feed = self._runtime.live_market
        feed.tick()
        if (
            self._capture_after_revision is not None
            and feed.revision > self._capture_after_revision
        ):
            self._capture_after_revision = None
            if feed.snapshot is not None and feed.enabled and feed.error is None:
                try:
                    record_snapshot_payload(feed.snapshot)
                except QuantLabError as exc:
                    self._runtime.record_notification(f"Kite snapshot not stored: {exc}")
                else:
                    self._runtime.record_notification(
                        "Kite quote snapshot captured; trading disabled"
                    )
        if self.isVisible():
            self.refresh()

    def refresh(self) -> None:
        feed = self._runtime.live_market
        self._kite_state.setText(f"Kite · {feed.status}")
        self._kite_state.setToolTip(feed.error or "Quotes only; broker account session is separate")
        self._kite_error.setText(feed.error or "")
        self._kite_error.setVisible(feed.error is not None)
        self._kite_connect.setEnabled(not feed.busy and not feed.enabled)
        self._kite_capture.setEnabled(self._capture_after_revision is None and not feed.busy)
        self._kite_capture.setText(
            "Capturing…" if self._capture_after_revision is not None else "Capture Kite snapshot"
        )
        last = last_run_row()
        if feed.snapshot is not None:
            last = feed.snapshot.model_dump(mode="json")
            last["id"] = feed.snapshot.snapshot_id
            last["hash"] = feed.snapshot.snapshot_hash
        if last is None:
            self.set_catalog_rows([])
            self.set_last_run(None)
            return
        update_table_values(
            self.catalog,
            self._catalog_headers,
            [
                ["Quality", str(last["quality"]), "data", "not silently valid"],
                ["Feed now", feed.status, "current", feed.error or "observe-only"],
                ["Freshness", str(last["freshness"]), "clock", "FRESH ≠ VALID"],
                ["Session", str(last["session"]), "calendar", "weekday IST"],
                [
                    "Source",
                    str(last.get("extras", {}).get("active_source", "unknown")),
                    "provenance",
                    "explicit",
                ],
                [
                    "Coverage",
                    str(last.get("extras", {}).get("coverage", "unknown")),
                    "health",
                    "not inferred",
                ],
                ["Hash", str(last["hash"]), "identity", "immutable"],
            ],
        )
        self.last.setVisible(True)
        self._empty.setVisible(False)
        update_table_values(
            self.last,
            ["Field", "Value"],
            [
                ["Snapshot", str(last["id"])],
                ["Quality at capture", str(last["quality"])],
                ["Hash", str(last["hash"])],
                [
                    "Note",
                    "Quote observation only. LIVE TRADING DISABLED. CONNECTED ≠ HEALTHY.",
                ],
            ],
        )
