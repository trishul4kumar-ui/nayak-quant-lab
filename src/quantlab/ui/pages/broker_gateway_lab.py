from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QWidget

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.broker_gateway import (
    connect_payload,
    disconnect_payload,
    health_payload,
    inspect_payload,
    last_run_row,
    reconcile_payload,
    snapshot_payload,
)
from quantlab.ui.widgets.catalog_page import CatalogLabPage
from quantlab.ui.widgets.lab_shell import StatusBadge


class BrokerGatewayLabPage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Broker Gateway Lab",
            subtitle="Read-only account state. No order routing. LIVE remains disabled.",
            nayak_summary=(
                "What is the authoritative external account state, how does it "
                "reconcile with QUANT LAB, and can connectivity exist without "
                "weakening safety?"
            ),
            technical=(
                "This page queries quantlab.app.broker_gateway. "
                "Qt does not place, modify, or cancel orders, store secrets, "
                "or enable live trading. Kite uses a GET-only allowlist; mock data remains "
                "available for safe UI exploration."
            ),
            catalog_title="Gateway diagnostics",
            catalog_headers=["Field", "Value", "Kind", "Note"],
            last_title="Last broker snapshot",
            empty_title="No broker snapshot yet",
            empty_body=(
                "Choose Kite to inspect your configured read-only account, or use Mock for "
                "safe demonstration data. LIVE remains disabled."
            ),
            empty_action="CONNECT & SNAPSHOT",
            on_empty_action=self._snapshot,
        )
        self._runtime = runtime
        self._last_feedback = "Choose an adapter and connect."
        badges = QLabel("LIVE DISABLED  ·  READ-ONLY  ·  NO ORDER ROUTING  ·  NO SECRETS")
        badges.setWordWrap(True)
        self.body().addWidget(badges)
        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)
        self._adapter = QComboBox()
        self._adapter.addItem("Kite — account observer (read-only)", "kite")
        self._adapter.addItem("Mock — safe demo account", "mock")
        self._connect = QPushButton("Connect")
        self._connect.setObjectName("primary")
        self._connect.clicked.connect(self._connect_adapter)
        self._snapshot_button = QPushButton("Refresh snapshot")
        self._snapshot_button.clicked.connect(self._snapshot)
        self._reconcile = QPushButton("Reconcile")
        self._reconcile.clicked.connect(self._reconcile_account)
        self._disconnect = QPushButton("Disconnect")
        self._disconnect.clicked.connect(self._disconnect_adapter)
        controls_layout.addWidget(self._adapter, 1)
        controls_layout.addWidget(self._connect)
        controls_layout.addWidget(self._snapshot_button)
        controls_layout.addWidget(self._reconcile)
        controls_layout.addWidget(self._disconnect)
        self.insert_before_last_run(controls)
        self._connection_badge = StatusBadge("off", text="DISCONNECTED")
        self.add_toolbar_widget(self._connection_badge)
        self.refresh()

    def _adapter_name(self) -> str:
        return str(self._adapter.currentData() or "mock")

    def _connect_adapter(self) -> None:
        adapter = self._adapter_name()
        self.show_interaction_feedback(f"Action received: {adapter} read-only connect")
        result = connect_payload(adapter=adapter)
        if error := result.get("error"):
            self._last_feedback = (
                f"{adapter.title()} could not connect: {error}. "
                "No account state was changed."
            )
        else:
            self._last_feedback = (
                f"{adapter.title()} is connected as an account observer. "
                "Refresh snapshot to collect read-only state."
            )
        self.refresh()

    def _snapshot(self) -> None:
        adapter = self._adapter_name()
        self.show_interaction_feedback(f"Action received: {adapter} account snapshot")
        result = connect_payload(adapter=adapter)
        if error := result.get("error"):
            self._last_feedback = f"Snapshot not captured: {error}. No account state was changed."
            self.refresh()
            return
        try:
            item = snapshot_payload()
        except Exception as exc:  # app facade gives model output; retain a visible safe failure.
            self._last_feedback = (
                f"Snapshot not captured: {type(exc).__name__}. No account state changed."
            )
        else:
            bundle_id = str(item.get("bundle_id", "captured"))[:28]
            self._last_feedback = (
                f"Immutable {adapter.title()} read-only snapshot {bundle_id} "
                "captured."
            )
        self.refresh()

    def _reconcile_account(self) -> None:
        self.show_interaction_feedback("Action received: account reconciliation")
        try:
            result = reconcile_payload()
        except Exception as exc:  # reconciliation must never disguise unavailable broker state.
            self._last_feedback = (
                f"Reconciliation not run: {type(exc).__name__}. No repair was attempted."
            )
        else:
            self._last_feedback = (
                f"Reconciliation complete: {result.get('status', 'unknown')}. "
                "This result cannot authorize or create an order."
            )
        self.refresh()

    def _disconnect_adapter(self) -> None:
        self.show_interaction_feedback("Action received: read-only disconnect")
        disconnect_payload()
        self._last_feedback = "Read-only session disconnected. No broker state was changed."
        self.refresh()

    def refresh(self) -> None:
        status = health_payload()
        state = str(status.get("state", "disconnected"))
        connected = bool(status.get("broker_connected", False))
        self._connection_badge.setText("CONNECTED · READ-ONLY" if connected else "DISCONNECTED")
        self._connection_badge.setStyleSheet(
            "background: #1a2e28; color: #26a69a; padding: 2px 8px; "
            "border-radius: 4px; font-size: 11px; font-weight: 600;"
            if connected
            else "background: #252932; color: #9aa1ad; padding: 2px 8px; "
            "border-radius: 4px; font-size: 11px; font-weight: 600;"
        )
        last = last_run_row()
        self.set_catalog_rows(
            [
                ["Adapter", self._adapter_name(), "selection", "GET-only observation"],
                ["State", state, "connection", "not live"],
                [
                    "Session",
                    "connected" if connected else "not connected",
                    "health",
                    "read-only only",
                ],
                ["Safety", "live disabled", "gate", "no order routing"],
                ["Last action", self._last_feedback, "operator", "visible local feedback"],
            ]
        )
        if last is None:
            self.set_last_run(None)
            return
        inspected = inspect_payload(str(last["id"]))
        account = inspected.get("account", {})
        self.set_last_run(
            [
                ("Snapshot", str(last["id"])),
                ("State", str(last["state"])),
                ("Hash", str(last["hash"])),
                ("Recon", str(last["recon"])),
                ("Available cash", str(account.get("available_cash", "—"))),
                ("Available margin", str(account.get("available_margin", "—"))),
                (
                    "Note",
                    "NOT LIVE. Kite is observation-only. "
                    "BROKER_CONNECTED ≠ TRADING_AUTHORIZED.",
                ),
            ]
        )
