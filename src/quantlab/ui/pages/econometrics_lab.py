from __future__ import annotations

from PySide6.QtWidgets import QLabel

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.econometrics import last_run_row, run_payload
from quantlab.ui.widgets.catalog_page import CatalogLabPage


class EconometricsLabPage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Econometrics Lab",
            subtitle="Stationarity, dependence, cointegration, Granger, breaks, panel, causal.",
            nayak_summary=(
                "Econometrics tests whether a relationship survives dependence, "
                "breaks, and multiple testing. Granger is not causation."
            ),
            technical=(
                "This page queries quantlab.app.econometrics. "
                "Qt does not fit models, parse Parquet, or write the ledger."
            ),
            catalog_title="Last econometric diagnostics",
            catalog_headers=["Field", "Value", "Kind", "Note"],
            last_title="Last econometric run",
            empty_title="No econometric run yet",
            empty_body="RUN ECONOMETRICS uses synthetic diagnostics. LIVE remains disabled.",
            empty_action="RUN ECONOMETRICS",
            on_empty_action=self._run,
        )
        self._runtime = runtime
        badges = QLabel("RESEARCH  ·  LIVE DISABLED  ·  correlation ≠ causation")
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
                ["Claim", str(last["claim"]), "predictive", "not causation"],
                ["Family", str(last["family"]), "FDR", "Prompt 14"],
                ["Hash", str(last["hash"]), "identity", "deterministic"],
            ]
        )
        self.set_last_run(
            [
                ("Econometric run", str(last["id"])),
                ("Claim", str(last["claim"])),
                ("Family", str(last["family"])),
                ("Hash", str(last["hash"])),
                ("Note", "SYNTHETIC. Not NSE. Not a claim. Prompt 05 remains the gate."),
            ]
        )
