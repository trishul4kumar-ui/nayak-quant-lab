from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.broker_gateway.service import last_snapshot
from quantlab.kite_execution_gateway.client import RemoteGatewayClient, RemoteGatewayError
from quantlab.kite_execution_gateway.models import (
    ManualLimitOrder,
    ManualOrderPreview,
    ManualOrderSubmission,
)
from quantlab.restricted_execution.repository import list_submissions
from quantlab.ui.widgets.catalog_page import CatalogLabPage
from quantlab.ui.widgets.lab_shell import StatusBadge


class RestrictedExecutionLabPage(CatalogLabPage):
    """One-at-a-time manual Kite limit-order ticket through the remote gateway."""

    def __init__(self, runtime: ApplicationRuntime) -> None:
        self._runtime = runtime
        self._preview: ManualOrderPreview | None = None
        self._draft: ManualLimitOrder | None = None
        super().__init__(
            "Manual Execution Console",
            subtitle="One human-confirmed order at a time through the separate Kite gateway.",
            nayak_summary=(
                "Create an exact NSE cash limit order, review its immutable hash, type the "
                "confirmation phrase and your authenticator code, then confirm the final dialog."
            ),
            technical=(
                "The desktop has no Kite API secret or access token. It sends HTTPS requests "
                "only to your separately deployed gateway, which permits NSE/CNC/LIMIT/DAY "
                "orders from its explicit allowlist and records idempotency before its one request."
            ),
            catalog_title="Local restricted-gateway history",
            catalog_headers=["Envelope", "State", "Correlation", "Detail"],
            last_title="Manual ticket status",
            empty_title="No local restricted-gateway attempts",
            empty_body=(
                "The remote gateway must be configured and authenticated before a ticket "
                "can preview."
            ),
            empty_action="REFRESH STATUS",
            on_empty_action=self.refresh,
        )
        badge = QLabel("REMOTE GATEWAY REQUIRED  ·  ONE ORDER  ·  TOTP + EXACT HASH  ·  NO RETRIES")
        badge.setWordWrap(True)
        self.body().addWidget(badge)
        self._remote_badge = StatusBadge("off", text="REMOTE GATEWAY UNCONFIGURED")
        self.add_toolbar_widget(self._remote_badge)
        self.insert_before_last_run(self._build_ticket())
        self.refresh()

    def _build_ticket(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        root = QVBoxLayout(frame)
        root.setContentsMargins(16, 16, 16, 16)
        title = QLabel("Manual Kite limit-order ticket")
        title.setStyleSheet("font-size: 14px; font-weight: 700;")
        root.addWidget(title)
        form = QFormLayout()
        self._symbol = QLineEdit("INFY")
        self._side = QComboBox()
        self._side.addItems(["BUY", "SELL"])
        self._quantity = QSpinBox()
        self._quantity.setRange(1, 100_000)
        self._quantity.setValue(1)
        self._price = QDoubleSpinBox()
        self._price.setRange(0.01, 10_000_000.0)
        self._price.setDecimals(2)
        self._price.setValue(1.0)
        self._price.setPrefix("₹ ")
        self._confirmation = QLineEdit()
        self._confirmation.setPlaceholderText("Type CONFIRM <exact hash> after preview")
        self._totp = QLineEdit()
        self._totp.setEchoMode(QLineEdit.EchoMode.Password)
        self._totp.setInputMask("000000")
        self._totp.setPlaceholderText("Authenticator code")
        form.addRow("Exchange", QLabel("NSE · cash delivery (CNC)"))
        form.addRow("Symbol", self._symbol)
        form.addRow("Side", self._side)
        form.addRow("Quantity", self._quantity)
        form.addRow("Limit price", self._price)
        form.addRow("Exact confirmation", self._confirmation)
        form.addRow("Operator TOTP", self._totp)
        root.addLayout(form)
        controls = QHBoxLayout()
        self._open_login = QPushButton("Open Kite login")
        self._open_login.clicked.connect(self._open_kite_login)
        self._preview_button = QPushButton("Preview exact order")
        self._preview_button.setObjectName("primary")
        self._preview_button.clicked.connect(self._preview_order)
        self._submit_button = QPushButton("Submit exact order")
        self._submit_button.setEnabled(False)
        self._submit_button.clicked.connect(self._submit_order)
        controls.addWidget(self._open_login)
        controls.addWidget(self._preview_button)
        controls.addWidget(self._submit_button)
        controls.addStretch()
        root.addLayout(controls)
        self._ticket_status = QLabel("Preview is required before submission.")
        self._ticket_status.setWordWrap(True)
        self._ticket_status.setObjectName("nayakVoice")
        root.addWidget(self._ticket_status)
        return frame

    def _client(self) -> RemoteGatewayClient:
        return RemoteGatewayClient()

    def _open_kite_login(self) -> None:
        self.show_interaction_feedback("Action received: secure Kite login")
        try:
            url = self._client().login_url()
        except RemoteGatewayError as exc:
            self._set_ticket_error(str(exc))
            return
        QDesktopServices.openUrl(QUrl(url))
        self._ticket_status.setText(
            "Kite login opened in your browser. The registered HTTPS callback exchanges the "
            "temporary token without exposing the API secret in this desktop application."
        )
        self.refresh()

    def _preview_order(self) -> None:
        self.show_interaction_feedback("Action received: manual order preview")
        try:
            draft = self._new_draft()
            preview = self._client().preview(draft)
        except (RemoteGatewayError, ValueError) as exc:
            self._set_ticket_error(str(exc))
            return
        self._draft = draft
        self._preview = preview
        self._submit_button.setEnabled(True)
        expiry = preview.expires_at.astimezone(UTC).strftime("%H:%M:%S UTC")
        self._ticket_status.setText(
            f"Preview hash: {preview.intent_hash}. "
            f"Estimated notional: ₹{preview.estimated_notional:,.2f}. "
            f"Expires at {expiry}. Type the exact confirmation and a fresh TOTP."
        )

    def _submit_order(self) -> None:
        if self._preview is None or self._draft is None:
            self._set_ticket_error("preview the exact order before submitting")
            return
        confirmation = self._confirmation.text().strip()
        if confirmation != self._preview.confirmation_text:
            self._set_ticket_error("exact hash confirmation does not match the preview")
            return
        code = self._totp.text()
        if len(code) != 6 or not code.isdigit():
            self._set_ticket_error("enter a current six-digit operator TOTP")
            return
        prompt = (
            f"Submit exactly this order?\n\n{self._side.currentText()} {self._quantity.value()} "
            f"NSE:{self._symbol.text().strip().upper()} at ₹{self._price.value():.2f}\n\n"
            "This sends one real Kite request through your remote gateway."
        )
        result = QMessageBox.warning(
            self,
            "Final manual order confirmation",
            prompt,
            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.Cancel,
        )
        if result is not QMessageBox.StandardButton.Yes:
            self._ticket_status.setText("Order submission cancelled. Nothing was sent to Kite.")
            return
        self.show_interaction_feedback("Action received: exact manual order submission")
        try:
            response = self._client().submit(
                ManualOrderSubmission(
                    order=self._draft,
                    intent_hash=self._preview.intent_hash,
                    confirmation_text=confirmation,
                    totp_code=code,
                )
            )
        except RemoteGatewayError as exc:
            self._set_ticket_error(str(exc))
            return
        self._submit_button.setEnabled(False)
        self._totp.clear()
        order_id = response.broker_order_id or "unknown — reconcile before any action"
        self._ticket_status.setText(
            f"Gateway state: {response.state.value}. Broker order ID: {order_id}. {response.detail}"
        )
        self._preview = None
        self._draft = None
        self.refresh()

    def _new_draft(self) -> ManualLimitOrder:
        bundle = last_snapshot()
        if bundle is None:
            raise ValueError(
                "capture a fresh read-only Broker Gateway snapshot before creating a ticket"
            )
        now = datetime.now(tz=UTC)
        return ManualLimitOrder(
            client_request_id=f"desktop-{uuid4()}",
            idempotency_key=f"desktop-{uuid4()}",
            account_fingerprint=bundle.profile.account_id_hash,
            exchange="NSE",
            tradingsymbol=self._symbol.text().strip().upper(),
            transaction_type=self._side.currentText(),
            quantity=self._quantity.value(),
            product="CNC",
            order_type="LIMIT",
            price=self._price.value(),
            validity="DAY",
            created_at=now,
            expires_at=now + timedelta(minutes=2),
        )

    def _set_ticket_error(self, detail: str) -> None:
        self._submit_button.setEnabled(False)
        self._ticket_status.setText(f"Order was not sent: {detail}")

    def refresh(self) -> None:
        try:
            status = self._client().health()
        except RemoteGatewayError:
            self._remote_badge.setText("REMOTE GATEWAY UNCONFIGURED")
            self._remote_badge.setStyleSheet(
                "background: #252932; color: #9aa1ad; padding: 2px 8px;"
            )
        else:
            ready = bool(status.get("ready", False))
            self._remote_badge.setText(
                "KITE MANUAL GATEWAY READY" if ready else "KITE LOGIN REQUIRED"
            )
            self._remote_badge.setStyleSheet(
                "background: #1a2e28; color: #26a69a; padding: 2px 8px;"
                if ready
                else "background: #2e2a1a; color: #ffb74d; padding: 2px 8px;"
            )
        items = list_submissions()
        self.set_catalog_rows(
            [
                [item.envelope_hash[:16], item.state.value, item.correlation_id, item.detail]
                for item in items
            ]
        )
        self.set_last_run(None)
