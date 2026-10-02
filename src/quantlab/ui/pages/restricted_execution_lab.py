# ruff: noqa: E501
from __future__ import annotations

from PySide6.QtWidgets import QLabel

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.restricted_execution.repository import list_submissions
from quantlab.ui.widgets.catalog_page import CatalogLabPage


class RestrictedExecutionLabPage(CatalogLabPage):
    """Visibility-only console for the disabled restricted execution boundary."""

    def __init__(self, runtime: ApplicationRuntime) -> None:
        del runtime
        super().__init__(
            "Restricted Execution Console",
            subtitle="Hash-bound human confirmation boundary. Broker writing is disabled.",
            nayak_summary="Review exact immutable requests and reconciliation outcomes; this page cannot submit an order.",
            technical="The bundled gateway has no production write adapter. Timeouts become SUBMISSION_UNKNOWN and require read-only reconciliation.",
            catalog_title="Gateway attempts",
            catalog_headers=["Envelope", "State", "Correlation", "Detail"],
            last_title="Gateway safety posture",
            empty_title="No gateway attempts",
            empty_body="The gateway starts disabled and never generates a trade, size, or route.",
            empty_action="REFRESH STATUS",
            on_empty_action=self.refresh,
        )
        badge = QLabel("LIVE DISABLED  ·  NO BROKER WRITE ADAPTER  ·  HUMAN CONFIRMATION REQUIRED")
        badge.setWordWrap(True)
        self.body().addWidget(badge)
        self.refresh()

    def refresh(self) -> None:
        items = list_submissions()
        self.set_catalog_rows(
            [
                [item.envelope_hash[:16], item.state.value, item.correlation_id, item.detail]
                for item in items
            ]
        )
        if not items:
            self.set_last_run(None)
            return
        item = items[-1]
        self.set_last_run(
            [
                ("State", item.state.value),
                ("Attempts", str(item.attempt_count)),
                ("Broker order ID", item.broker_order_id or "—"),
                ("Rule", "SUBMISSION_UNKNOWN is never automatically retried."),
            ]
        )
