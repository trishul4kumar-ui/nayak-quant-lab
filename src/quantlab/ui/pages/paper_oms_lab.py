from __future__ import annotations

from PySide6.QtWidgets import QLabel

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.paper_oms import last_run_row, policy_rows, submit_payload
from quantlab.ui.widgets.catalog_page import CatalogLabPage


class PaperOMSLabPage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Paper OMS Lab",
            subtitle="Paper order lifecycle from a target portfolio — not a live broker.",
            nayak_summary=(
                "Paper OMS turns an immutable investment decision into simulated orders, "
                "fills, positions, and reconciliation. "
                "A paper fill is never a broker confirmation."
            ),
            technical=(
                "This page is a query view of quantlab.app.paper_oms. "
                "Qt does not parse Parquet, query DuckDB, compute targets, "
                "mutate orders directly, or import brokers. "
                "SUBMIT PAPER runs the local simulator only."
            ),
            catalog_title="Paper execution policies",
            catalog_headers=["Policy", "Scenario", "Model", "Seed"],
            last_title="Last paper OMS run",
            empty_title="No paper OMS run yet",
            empty_body="SUBMIT PAPER simulates the seed target. LIVE remains disabled.",
            empty_action="SUBMIT PAPER",
            on_empty_action=self._submit_paper,
        )
        self._runtime = runtime
        badges = QLabel("PAPER  ·  LIVE DISABLED  ·  fills are simulated, not BROKER CONFIRMED")
        badges.setWordWrap(True)
        self.body().addWidget(badges)
        self.refresh()

    def _submit_paper(self) -> None:
        submit_payload("last")
        self.refresh()

    def refresh(self) -> None:
        self.set_catalog_rows(policy_rows())
        last = last_run_row()
        if last is None:
            self.set_last_run(None)
            return
        self.set_last_run(
            [
                ("OMS run", str(last["id"])),
                ("Status", str(last["status"])),
                ("Reconciliation", str(last["recon"])),
                ("Orders", str(last["orders"])),
                ("Fills", str(last["fills"])),
                ("Cash", str(last["cash"])),
                ("Hash", str(last["hash"])),
                ("Note", "PAPER. Not LIVE FILLED. Not BROKER CONFIRMED."),
            ]
        )
