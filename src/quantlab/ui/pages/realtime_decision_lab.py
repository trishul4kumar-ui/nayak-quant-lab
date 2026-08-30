from __future__ import annotations

from PySide6.QtWidgets import QLabel

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.realtime_decision import last_run_row, run_payload
from quantlab.ui.widgets.catalog_page import CatalogLabPage


class RealTimeDecisionLabPage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Real-Time Decision Lab",
            subtitle="Target portfolio is not an order. Abstention is first-class.",
            nayak_summary=(
                "Given a frozen snapshot and an explicit strategy release, what would "
                "QUANT LAB decide — and when must it abstain?"
            ),
            technical=(
                "This page queries quantlab.app.realtime_decision. "
                "Qt cannot certify, promote, authorize, or create live orders. "
                "RUN DECISION is local only."
            ),
            catalog_title="Decision diagnostics",
            catalog_headers=["Field", "Value", "Kind", "Note"],
            last_title="Last realtime decision",
            empty_title="No realtime decision yet",
            empty_body="RUN DECISION uses the uncertified default release and may abstain.",
            empty_action="RUN DECISION",
            on_empty_action=self._run,
        )
        self._runtime = runtime
        badges = QLabel("LIVE DISABLED  ·  DECISION ≠ ORDER  ·  NO BROKER")
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
                ["State", str(last["state"]), "cycle", "not an order"],
                ["Abstention", str(last["abstention"]), "decision", "first-class"],
                ["Hash", str(last["hash"]), "identity", "deterministic"],
                ["Portfolio", str(last["portfolio"]), "target", "not an order"],
            ]
        )
        self.set_last_run(
            [
                ("Decision", str(last["id"])),
                ("State", str(last["state"])),
                ("Abstention", str(last["abstention"])),
                ("Hash", str(last["hash"])),
                ("Note", "NOT LIVE. DECISION ≠ ORDER. TargetPortfolio is terminal."),
            ]
        )
