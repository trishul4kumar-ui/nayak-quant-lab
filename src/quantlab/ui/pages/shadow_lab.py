from __future__ import annotations

from PySide6.QtWidgets import QLabel

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.shadow import last_run_row, run_payload
from quantlab.ui.widgets.catalog_page import CatalogLabPage


class ShadowLabPage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Shadow Trading Lab",
            subtitle="Production-like paper and shadow cycles. No broker routing.",
            nayak_summary=(
                "If QUANT LAB were operating now, what would it decide and how would "
                "the books evolve — without sending a broker order? Paper profit is "
                "not validated alpha. Shadow execution is not broker execution."
            ),
            technical=(
                "This page queries quantlab.app.shadow. "
                "Qt does not parse Parquet, fit models, simulate fills, write the ledger, "
                "bypass certification, or connect brokers. RUN SHADOW is local only."
            ),
            catalog_title="Last shadow diagnostics",
            catalog_headers=["Field", "Value", "Kind", "Note"],
            last_title="Last shadow cycle",
            empty_title="No shadow cycle yet",
            empty_body="RUN SHADOW uses the synthetic seed. LIVE remains disabled.",
            empty_action="RUN SHADOW",
            on_empty_action=self._run,
        )
        self._runtime = runtime
        badges = QLabel("PAPER  ·  SHADOW  ·  LIVE DISABLED  ·  NO BROKER ROUTING")
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
                ["Mode", str(last["mode"]), "engine", "not live"],
                ["Status", str(last["status"]), "cycle", "not broker"],
                ["Recon", str(last["recon"]), "identity", "breaks retained"],
                ["Hash", str(last["hash"]), "identity", "deterministic"],
            ]
        )
        self.set_last_run(
            [
                ("Cycle", str(last["id"])),
                ("Mode", str(last["mode"])),
                ("Status", str(last["status"])),
                ("Orders", str(last["orders"])),
                ("Fills", str(last["fills"])),
                ("Hash", str(last["hash"])),
                (
                    "Note",
                    "NOT LIVE. Shadow ≠ paper OMS ≠ broker. Prompt 05 remains the gate.",
                ),
            ]
        )
