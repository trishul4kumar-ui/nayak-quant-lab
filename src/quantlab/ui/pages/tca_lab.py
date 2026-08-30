from __future__ import annotations

from PySide6.QtWidgets import QLabel

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.tca import last_run_row, run_payload
from quantlab.ui.widgets.catalog_page import CatalogLabPage


class TCALabPage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "TCA & Capacity Lab",
            subtitle="Implementation shortfall, calibration, capacity, and fragility.",
            nayak_summary=(
                "TCA measures how much of an edge survives execution assumptions. "
                "Capacity is policy-defined. Synthetic volume is not NSE ADV."
            ),
            technical=(
                "This page queries quantlab.app.tca. "
                "Qt does not parse Parquet, calibrate models, or import brokers. "
                "RUN TCA uses paper fills only."
            ),
            catalog_title="Last TCA diagnostics",
            catalog_headers=["Field", "Value", "Kind", "Note"],
            last_title="Last TCA run",
            empty_title="No TCA run yet",
            empty_body="RUN TCA measures paper fills. LIVE remains disabled.",
            empty_action="RUN TCA",
            on_empty_action=self._run_tca,
        )
        self._runtime = runtime
        badges = QLabel("PAPER  ·  LIVE DISABLED  ·  modelled ≠ observed  ·  not NSE ADV")
        badges.setWordWrap(True)
        self.body().addWidget(badges)
        self.refresh()

    def _run_tca(self) -> None:
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
                ["Kind", str(last["kind"]), "tca", "not broker"],
                ["Shortfall", str(last["shortfall"]), "IS", "simulated"],
                ["Fragility", str(last["fragility"]), "surface", "not a gate"],
                ["Hash", str(last["hash"]), "identity", "deterministic"],
            ]
        )
        self.set_last_run(
            [
                ("TCA run", str(last["id"])),
                ("Kind", str(last["kind"])),
                ("Shortfall", str(last["shortfall"])),
                ("Fragility", str(last["fragility"])),
                ("Hash", str(last["hash"])),
                ("Note", "PAPER. Not LIVE. Not BROKER TCA. Not NSE ADV."),
            ]
        )
