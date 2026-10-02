from __future__ import annotations

from PySide6.QtWidgets import QLabel

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.execution_authorization import last_run_row, run_payload
from quantlab.ui.widgets.catalog_page import CatalogLabPage


class ExecutionAuthorizationLabPage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Execution Authorization Lab",
            subtitle="Eligibility governance only. It cannot route, arm, or submit orders.",
            nayak_summary=(
                "Which evidence would be required for a human to review a precise restricted-live "
                "scope, while preserving the hard execution safety wall?"
            ),
            technical=(
                "This page only queries quantlab.app.execution_authorization. Human approval "
                "requires an exact package hash and is not a trading action."
            ),
            catalog_title="Eligibility checks",
            catalog_headers=["Field", "Value", "Kind", "Note"],
            last_title="Latest immutable assessment",
            empty_title="No authorization assessment yet",
            empty_body="RUN ASSESSMENT identifies missing evidence. It cannot grant authorization.",
            empty_action="RUN ASSESSMENT",
            on_empty_action=self._run,
        )
        self._runtime = runtime
        badge = QLabel("LIVE DISABLED  ·  HUMAN REVIEW ONLY  ·  NO ORDER ROUTING")
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
        self.set_catalog_rows(
            [
                ["State", str(item["state"]), "governance", "automatic evaluation cannot approve"],
                [
                    "Blockers",
                    str(len(item["blockers"])),
                    "evidence",
                    "critical missing evidence blocks",
                ],
                ["Policy", str(item["policy"]["policy_version"]), "policy", "versioned"],
                ["Hash", str(item["assessment_hash"]), "identity", "scope-bound"],
            ]
        )
        self.set_last_run(
            [
                ("Assessment", str(item["assessment_id"])),
                ("State", str(item["state"])),
                ("Hash", str(item["assessment_hash"])),
                ("Note", "RELEASE_ELIGIBLE ≠ EXECUTION_AUTHORIZED."),
            ]
        )
