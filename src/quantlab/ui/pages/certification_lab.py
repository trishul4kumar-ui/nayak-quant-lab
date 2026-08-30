from __future__ import annotations

from PySide6.QtWidgets import QLabel

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.certification import last_run_row, run_payload
from quantlab.ui.widgets.catalog_page import CatalogLabPage


class CertificationLabPage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Validation & Certification Lab",
            subtitle="Independent validation, model risk, and pre-live certification.",
            nayak_summary=(
                "Certification asks whether a model may progress to the next controlled "
                "stage. CERTIFIED is not live. Qt cannot force certification."
            ),
            technical=(
                "This page queries quantlab.app.certification. "
                "Qt does not change certification state, waive findings, or enable live."
            ),
            catalog_title="Last certification diagnostics",
            catalog_headers=["Field", "Value", "Kind", "Note"],
            last_title="Last certification candidate",
            empty_title="No certification candidate yet",
            empty_body="RUN VALIDATION uses the seed candidate. LIVE remains disabled.",
            empty_action="RUN VALIDATION",
            on_empty_action=self._run,
        )
        self._runtime = runtime
        badges = QLabel("GOVERNANCE  ·  LIVE DISABLED  ·  research ≠ certified ≠ live")
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
                ["State", str(last["state"]), "machine", "not live"],
                ["Blocked", str(last["blocked"]), "policy", "FAIL blocks"],
                ["Hash", str(last["hash"]), "identity", "deterministic"],
            ]
        )
        self.set_last_run(
            [
                ("Certification", str(last["id"])),
                ("Candidate", str(last["candidate"])),
                ("State", str(last["state"])),
                ("Blocked", str(last["blocked"])),
                ("Hash", str(last["hash"])),
                ("Note", "NOT LIVE. CERTIFIED ≠ broker permission. Prompt 05 remains the gate."),
            ]
        )
