from __future__ import annotations

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.orchestration import hypothesis_rows, last_orchestration_experiment_row
from quantlab.ui.widgets.catalog_page import CatalogLabPage


class ResearchControlPage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Research Control",
            subtitle="What was tested, with which information, under which PIT constraints.",
            nayak_summary=(
                "The control plane records hypotheses, families, and every candidate. "
                "Discovery is not confirmation. Synthetic results cannot promote. "
                "A failed hypothesis is a valid scientific result."
            ),
            technical=(
                "Orchestration calls existing engines. Prompt 05 remains the only gate. "
                "The UI does not run grids or fit models."
            ),
            catalog_title="Registered hypotheses",
            catalog_headers=["Hypothesis", "Status", "Null", "Identity"],
            last_title="Last orchestration experiment",
            empty_title="No orchestration runs yet",
            empty_body="Run quantlab research discover from the CLI. Results appear here.",
            empty_action=None,
            dashboard_titles=["Candidates", "Tested", "Gate", "Hypothesis"],
        )
        self._runtime = runtime
        self.refresh()

    def refresh(self) -> None:
        self.set_catalog_rows(
            [
                [
                    str(row["hypothesis_id"]),
                    str(row["status"]),
                    str(row["null_hypothesis"]),
                    str(row["identity"]),
                ]
                for row in hypothesis_rows()
            ]
        )
        last = last_orchestration_experiment_row(self._runtime)
        dash = self.dashboard
        if last is None:
            self.set_last_run(None)
            if dash is not None:
                for card in dash.cards:
                    card.set_value("—")
            return
        if dash is not None:
            dash.card(0).set_value(str(last.get("candidate_count", "—")))
            dash.card(1).set_value(str(last.get("tested_count", "—")))
            dash.card(2).set_value(str(last.get("gate_outcome", "—"))[:12])
            dash.card(3).set_value(str(last.get("hypothesis_id", "—"))[:14])
        self.set_last_run(
            [
                ("Ledger id", str(last["id"])),
                ("Experiment", str(last["orchestration_id"])),
                ("Hypothesis", str(last["hypothesis_id"])),
                ("Family", str(last["family_id"])),
                ("Gate", str(last["gate_outcome"])),
                ("Data", str(last["data_kind"])),
                ("Candidates", str(last["candidate_count"])),
                ("Tested", str(last["tested_count"])),
                ("Identity", str(last["identity"])),
            ]
        )
