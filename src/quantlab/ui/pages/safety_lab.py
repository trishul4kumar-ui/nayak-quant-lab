from __future__ import annotations

from PySide6.QtWidgets import QLabel

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.safety import last_run_row, run_payload
from quantlab.ui.widgets.catalog_page import CatalogLabPage


class SafetyLabPage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Safety & Control Lab",
            subtitle="Live-boundary gates. Authorization is not a broker submit.",
            nayak_summary=(
                "If an execution request were presented to the live boundary, is it "
                "authorized, valid, reconciled, and safe — or must it be rejected? "
                "LIVE remains disabled. This page cannot send an order."
            ),
            technical=(
                "This page queries quantlab.app.safety. "
                "Qt does not calculate risk, mutate policy, write the ledger, "
                "bypass authorization, or connect brokers. RUN SAFETY is local only."
            ),
            catalog_title="Last safety diagnostics",
            catalog_headers=["Field", "Value", "Kind", "Note"],
            last_title="Last safety evaluation",
            empty_title="No safety evaluation yet",
            empty_body="RUN SAFETY evaluates G0–G15. LIVE remains disabled.",
            empty_action="RUN SAFETY",
            on_empty_action=self._run,
        )
        self._runtime = runtime
        badges = QLabel("LIVE DISABLED  ·  BLOCKED  ·  NO BROKER ROUTING  ·  G15 BLOCK")
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
                ["State", str(last["state"]), "gateway", "not live"],
                ["Blocked", str(last["blocked"]), "gate", "fail closed"],
                ["Hash", str(last["hash"]), "identity", "deterministic"],
                ["Gates", str(last["gates"]), "G0-G15", "NOT_TESTED ≠ PASS"],
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
                    "NOT LIVE. Authorization ≠ broker submit. Prompt 05 remains the gate.",
                ),
            ]
        )
