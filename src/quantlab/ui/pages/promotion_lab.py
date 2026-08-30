from __future__ import annotations

from PySide6.QtWidgets import QLabel

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.release import last_run_row, run_payload
from quantlab.ui.widgets.catalog_page import CatalogLabPage


class PromotionLabPage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Certification & Promotion Lab",
            subtitle="Release eligibility. CERTIFIED is not live. No broker routing.",
            nayak_summary=(
                "Has QUANT LAB accumulated enough independent evidence to make a "
                "controlled live release *eligible*? Eligibility is not permission to trade."
            ),
            technical=(
                "This page queries quantlab.app.release. "
                "Qt does not certify, mutate evidence, write the ledger, enable live, "
                "or import broker SDKs. RUN CERTIFICATION is local only."
            ),
            catalog_title="Certification diagnostics",
            catalog_headers=["Field", "Value", "Kind", "Note"],
            last_title="Last certification evaluation",
            empty_title="No live-certification package yet",
            empty_body="RUN CERTIFICATION evaluates domains. LIVE remains disabled.",
            empty_action="RUN CERTIFICATION",
            on_empty_action=self._run,
        )
        self._runtime = runtime
        badges = QLabel(
            "LIVE DISABLED  ·  CERTIFIED ≠ LIVE  ·  NO BROKER  ·  SAFETY NOT WAIVABLE"
        )
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
                ["State", str(last["state"]), "governance", "not live"],
                ["Blocked", str(last["blocked"]), "gate", "fail closed"],
                ["Hash", str(last["hash"]), "identity", "immutable"],
                ["Criteria", str(last["criteria"]), "domains", "NOT_TESTED ≠ PASS"],
            ]
        )
        self.set_last_run(
            [
                ("Evaluation", str(last["id"])),
                ("State", str(last["state"])),
                ("Blocked", str(last["blocked"])),
                ("Hash", str(last["hash"])),
                (
                    "Note",
                    "NOT LIVE. Prompt 23 remains model-risk validation. "
                    "Prompt 05 remains the gate.",
                ),
            ]
        )
