# ruff: noqa: E501
from __future__ import annotations

from PySide6.QtWidgets import QLabel

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.live_ops.repository import last_snapshot
from quantlab.live_ops.service import LiveOperationsService
from quantlab.ui.widgets.catalog_page import CatalogLabPage


class LiveOperationsLabPage(CatalogLabPage):
    """Operations centre with observation and containment, never execution authority."""

    def __init__(self, runtime: ApplicationRuntime) -> None:
        del runtime
        super().__init__(
            "Live Operations Center",
            subtitle="Health, alert, incident, and containment visibility. It cannot trade or resume automatically.",
            nayak_summary="Collect evidence, deduplicate alerts, and guide a human incident response without changing a portfolio.",
            technical="Critical incidents can request investigation or invoke the existing kill switch only when an explicit policy permits it. Automatic recovery is absent.",
            catalog_title="Operational health signals",
            catalog_headers=["Component", "Status", "Evidence", "Detail"],
            last_title="Latest operations snapshot",
            empty_title="No operations snapshot yet",
            empty_body="RUN HEALTH collects local evidence; unavailable observations remain explicit rather than assumed healthy.",
            empty_action="RUN HEALTH",
            on_empty_action=self._run,
        )
        self._service = LiveOperationsService()
        badge = QLabel("LIVE DISABLED  ·  MONITORING ONLY  ·  NO AUTOMATIC RESUME")
        badge.setWordWrap(True)
        self.body().addWidget(badge)
        self.refresh()

    def _run(self) -> None:
        self._service.collect()
        self.refresh()

    def refresh(self) -> None:
        snapshot = last_snapshot()
        if snapshot is None:
            self.set_catalog_rows([])
            self.set_last_run(None)
            return
        self.set_catalog_rows(
            [
                [signal.component, signal.status, str(len(signal.evidence)), signal.detail]
                for signal in snapshot.signals
            ]
        )
        self.set_last_run(
            [
                ("Alerts", str(len(snapshot.alerts))),
                ("Incidents", str(len(snapshot.incidents))),
                ("Safe actions", str(len(snapshot.actions))),
                ("Rule", "No auto-resume; human closure needs rationale and evidence."),
            ]
        )
