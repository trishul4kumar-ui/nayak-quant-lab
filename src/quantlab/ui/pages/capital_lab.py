from __future__ import annotations

from PySide6.QtWidgets import QLabel

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.capital import last_decision_row, policy_rows
from quantlab.ui.widgets.catalog_page import CatalogLabPage


class CapitalLabPage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Capital Lab",
            subtitle="How much capital, to which names, under which budget — not an order.",
            nayak_summary=(
                "Capital allocation produces target portfolios and investment decisions. "
                "It does not submit, modify, or route broker orders. "
                "Synthetic allocations remain research diagnostics."
            ),
            technical=(
                "This page is a query view of quantlab.app.capital. "
                "Qt does not compute allocations, query Parquet/DuckDB, import brokers, "
                "mutate decisions, or write the ledger."
            ),
            catalog_title="Capital policies",
            catalog_headers=["Policy", "CCY", "Capital", "Target vol", "Sizing"],
            last_title="Last investment decision",
            empty_title="No capital decision yet",
            empty_body="Run quantlab capital allocate mom20_topn to record a research target.",
            empty_action=None,
        )
        self._runtime = runtime
        note = QLabel("LIVE_TRADING remains false. Prompt 18 owns paper OMS.")
        note.setWordWrap(True)
        self.body().addWidget(note)
        self.refresh()

    def refresh(self) -> None:
        self.set_catalog_rows(policy_rows())
        last = last_decision_row(self._runtime.ledger)
        if last is None:
            self.set_last_run(None)
            return
        self.set_last_run(
            [
                ("Decision", str(last["id"])),
                ("Status", str(last["status"])),
                ("Capital state", str(last["capital_state"])),
                ("Gross", str(last["gross"])),
                ("Net", str(last["net"])),
                ("Vol", str(last["vol"])),
                ("Abstention", str(last["abstention"])),
                ("Hash", str(last["hash"])),
                ("Note", "Target only. Not a live book."),
            ]
        )
