from __future__ import annotations

from PySide6.QtWidgets import QLabel

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.digital_twin import last_run_row, run_payload
from quantlab.ui.widgets.catalog_page import CatalogLabPage


class DigitalTwinLabPage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Digital Twin / Shadow Lab",
            subtitle="Deterministic replay. Shadow is not live. Twin is not a broker.",
            nayak_summary=(
                "If the same events replayed, would QUANT LAB reach the same hashed "
                "state — without sending a broker order?"
            ),
            technical=(
                "This page queries quantlab.app.digital_twin. "
                "Qt cannot send orders, live-trade, or route to a broker. "
                "RUN SHADOW is local simulation only."
            ),
            catalog_title="Twin diagnostics",
            catalog_headers=["Field", "Value", "Kind", "Note"],
            last_title="Last twin run",
            empty_title="No twin run yet",
            empty_body="RUN SHADOW replays a deterministic cycle. LIVE remains disabled.",
            empty_action="RUN SHADOW",
            on_empty_action=self._run,
        )
        self._runtime = runtime
        badges = QLabel("LIVE DISABLED  ·  SHADOW ONLY  ·  ZERO BROKER WRITE")
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
                ["Mode", str(last["mode"]), "twin", "not live"],
                ["State", str(last["state"]), "lifecycle", "not broker"],
                ["Hash", str(last["hash"]), "identity", "deterministic"],
                ["Fill", str(last["fill"]), "simulated", "not broker confirmation"],
            ]
        )
        self.set_last_run(
            [
                ("Run", str(last["id"])),
                ("Mode", str(last["mode"])),
                ("Hash", str(last["hash"])),
                ("Decision", str(last["decision"])),
                (
                    "Note",
                    "NOT LIVE. SHADOW ≠ PAPER ≠ LIVE. DIGITAL TWIN ≠ BROKER. "
                    "Simulated fill ≠ broker confirmation.",
                ),
            ]
        )
