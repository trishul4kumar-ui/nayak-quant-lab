from __future__ import annotations

from PySide6.QtWidgets import QLabel

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.broker_gateway import last_run_row, run_payload
from quantlab.ui.widgets.catalog_page import CatalogLabPage


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
                "or enable live trading. RUN SNAPSHOT is local mock only."
            ),
            catalog_title="Gateway diagnostics",
            catalog_headers=["Field", "Value", "Kind", "Note"],
            last_title="Last broker snapshot",
            empty_title="No broker snapshot yet",
            empty_body="RUN SNAPSHOT captures a read-only mock account. LIVE remains disabled.",
            empty_action="RUN SNAPSHOT",
            on_empty_action=self._run,
        )
        self._runtime = runtime
        badges = QLabel("LIVE DISABLED  ·  READ-ONLY  ·  NO ORDER ROUTING  ·  NO SECRETS")
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
                ["State", str(last["state"]), "connection", "not live"],
                ["Hash", str(last["hash"]), "identity", "immutable"],
                ["Recon", str(last["recon"]), "account", "never silent repair"],
                ["Mode", "read-only", "safety", "no order routing"],
            ]
        )
        self.set_last_run(
            [
                ("Snapshot", str(last["id"])),
                ("State", str(last["state"])),
                ("Hash", str(last["hash"])),
                ("Recon", str(last["recon"])),
                (
                    "Note",
                    "NOT LIVE. Broker Console remains a separate wizard. "
                    "BROKER_CONNECTED ≠ TRADING_AUTHORIZED.",
                ),
            ]
        )
