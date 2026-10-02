from __future__ import annotations

from PySide6.QtWidgets import QLabel

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.reconciliation import last_run_row, run_payload
from quantlab.ui.widgets.catalog_page import CatalogLabPage


class ReconciliationLabPage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Account Reconciliation Lab",
            subtitle="Compare broker observations with internal state. Never repair or trade.",
            nayak_summary=(
                "Does QUANT LAB's cash, positions, holdings, orders and fills agree with "
                "the observed broker snapshot?"
            ),
            technical=(
                "This page queries quantlab.app.reconciliation. Qt never creates "
                "compensating orders, changes broker state, or treats a match as authorization."
            ),
            catalog_title="Reconciliation diagnostics",
            catalog_headers=["Field", "Value", "Kind", "Note"],
            last_title="Latest immutable report",
            empty_title="No reconciliation report yet",
            empty_body=(
                "RUN RECONCILIATION compares read-only mock snapshots. LIVE remains disabled."
            ),
            empty_action="RUN RECONCILIATION",
            on_empty_action=self._run,
        )
        self._runtime = runtime
        badges = QLabel("LIVE DISABLED  ·  READ-ONLY  ·  NO COMPENSATING ORDERS")
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
                ["Status", str(last["status"]), "comparison", "UNKNOWN never becomes MATCH"],
                ["Policy", str(last["policy_version"]), "tolerance", "versioned and explicit"],
                ["Exceptions", str(len(last["exceptions"])), "incident", "immutable evidence"],
                ["Hash", str(last["reconciliation_hash"]), "identity", "deterministic report"],
            ]
        )
        self.set_last_run(
            [
                ("Report", str(last["reconciliation_id"])),
                ("Status", str(last["status"])),
                ("Hash", str(last["reconciliation_hash"])),
                ("Note", "RECONCILE ≠ REPAIR. MISMATCH ≠ ORDER."),
            ]
        )
