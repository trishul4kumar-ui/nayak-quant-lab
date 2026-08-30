from __future__ import annotations

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.queries import adaptive_catalog_rows, last_adaptive_experiment_row
from quantlab.ui.widgets.catalog_page import CatalogLabPage


class AdaptivePage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Adaptive Lab",
            subtitle="Online learners that update predictions as new bars arrive.",
            nayak_summary=(
                "Adaptive models re-fit as data streams in. They can track drift — "
                "but adaptive improvement is not the same as finding alpha."
            ),
            technical=(
                "Predict-then-update policies run in the core engine; this page is read-only."
            ),
            catalog_title="Seed adaptive models",
            catalog_headers=["Model", "Policy", "Learner", "Alphas"],
            last_title="Last adaptive experiment",
            dashboard_titles=["Prequential IC", "Model", "Gate", "Data"],
        )
        self._runtime = runtime
        self.refresh()

    def refresh(self) -> None:
        self.set_catalog_rows(
            [
                [
                    str(row["adaptive_model_id"]),
                    str(row["policy"]),
                    str(row["learner"]),
                    str(row["alphas"]),
                ]
                for row in adaptive_catalog_rows()
            ]
        )
        last = last_adaptive_experiment_row(self._runtime)
        dash = self.dashboard
        if last is None:
            self.set_last_run(None)
            if dash is not None:
                for card in dash.cards:
                    card.set_value("—")
            return
        ic = last.get("prequential_ic")
        if dash is not None:
            dash.card(0).set_value("" if ic is None else str(ic))
            dash.card(1).set_value(str(last.get("adaptive_model_id", "—"))[:14])
            dash.card(2).set_value(str(last.get("gate_outcome", "—"))[:12])
            dash.card(3).set_value(str(last.get("data_kind", "—"))[:12])
        self.set_last_run(
            [
                ("experiment", str(last["id"])[:16]),
                ("model", str(last["adaptive_model_id"])),
                ("policy", str(last["policy"])),
                ("gate", str(last["gate_outcome"])),
                ("data", str(last["data_kind"])),
                (
                    "prequential_ic",
                    "" if last["prequential_ic"] is None else str(last["prequential_ic"]),
                ),
            ]
        )
