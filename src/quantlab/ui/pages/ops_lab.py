from __future__ import annotations

from PySide6.QtWidgets import QLabel

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.ops import last_run_row, run_payload
from quantlab.ui.widgets.catalog_page import CatalogLabPage


class OpsLabPage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Operations Control Lab",
            subtitle="Process, health, backup, and recovery. Not a broker console.",
            nayak_summary=(
                "If QUANT LAB were running as a production system, is the process "
                "alive, configured, healthy, recoverable, and observable — without "
                "placing a live order?"
            ),
            technical=(
                "This page queries quantlab.app.ops. "
                "Qt does not mutate safety-critical configuration, restore unverified "
                "backups, or connect brokers. RUN DOCTOR is local only."
            ),
            catalog_title="Control-plane diagnostics",
            catalog_headers=["Field", "Value", "Kind", "Note"],
            last_title="Last ops doctor",
            empty_title="No ops doctor yet",
            empty_body=(
                "RUN DOCTOR evaluates config, clock, disk, and health. LIVE remains disabled."
            ),
            empty_action="RUN DOCTOR",
            on_empty_action=self._run,
        )
        self._runtime = runtime
        badges = QLabel("LIVE DISABLED  ·  RESEARCH ENV  ·  NO BROKER ROUTING  ·  NO SECRETS")
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
                ["Environment", str(last["environment"]), "ops", "not live"],
                ["State", str(last["state"]), "lifecycle", "unknown ≠ healthy"],
                ["Health", str(last["health"]), "status", "not a trade"],
                ["Hash", str(last["hash"]), "identity", "config-bound"],
            ]
        )
        self.set_last_run(
            [
                ("Run", str(last["id"])),
                ("State", str(last["state"])),
                ("Health", str(last["health"])),
                ("Environment", str(last["environment"])),
                (
                    "Note",
                    "NOT LIVE. Ops ≠ safety gateway ≠ broker. LIVE_TRADING remains false.",
                ),
            ]
        )
