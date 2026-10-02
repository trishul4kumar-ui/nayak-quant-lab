from __future__ import annotations

from PySide6.QtWidgets import QLabel

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.production_shadow import last_run_row, run_payload
from quantlab.ui.widgets.catalog_page import CatalogLabPage


class ProductionShadowLabPage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Production Shadow Lab",
            subtitle="Observed-state evidence with simulated execution. Never routed.",
            nayak_summary=(
                "Can the observed feed, account, decision and simulated shadow cycle be "
                "trusted enough to produce evidence — without creating a broker instruction?"
            ),
            technical=(
                "This page only queries quantlab.app.production_shadow. It cannot send an "
                "order, enable live trading, or modify broker state."
            ),
            catalog_title="Production-shadow readiness",
            catalog_headers=["Field", "Value", "Kind", "Note"],
            last_title="Latest immutable production-shadow run",
            empty_title="No production-shadow run yet",
            empty_body="RUN ASSESSMENT fails closed until real, verifiable evidence is available.",
            empty_action="RUN ASSESSMENT",
            on_empty_action=self._run,
        )
        self._runtime = runtime
        badge = QLabel("LIVE DISABLED  ·  NON-ROUTABLE  ·  SIMULATED FILLS ONLY")
        badge.setWordWrap(True)
        self.body().addWidget(badge)
        self.refresh()

    def _run(self) -> None:
        run_payload()
        self.refresh()

    def refresh(self) -> None:
        item = last_run_row()
        if item is None:
            self.set_catalog_rows([])
            self.set_last_run(None)
            return
        failures = item["readiness"]["critical_failures"]
        self.set_catalog_rows(
            [
                ["State", str(item["state"]), "safety", "critical evidence fails closed"],
                ["Failures", str(len(failures)), "readiness", "not hidden by an aggregate score"],
                [
                    "Market",
                    str(item["evidence_labels"]["market"]),
                    "evidence",
                    "provenance required",
                ],
                ["Hash", str(item["run_hash"]), "identity", "immutable"],
            ]
        )
        self.set_last_run(
            [
                ("Run", str(item["shadow_run_id"])),
                ("State", str(item["state"])),
                ("Hash", str(item["run_hash"])),
                ("Note", "SHADOW ORDER ≠ BROKER ORDER. SIMULATED FILL ≠ BROKER FILL."),
            ]
        )
