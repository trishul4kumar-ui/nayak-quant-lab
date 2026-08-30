from __future__ import annotations

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.queries import last_learning_experiment_row, learning_catalog_rows
from quantlab.ui.widgets.catalog_page import CatalogLabPage


class LearningPage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Model Lab",
            subtitle="Statistical models that map features to expected returns.",
            nayak_summary=(
                "A model estimates relationships between features and outcomes. "
                "Strong out-of-sample IC is encouraging — but a model is not alpha by itself."
            ),
            technical=(
                "Walk-forward fitting stays in the core; hyperparameter search is not exposed here."
            ),
            catalog_title="Seed statistical models",
            catalog_headers=["Model", "Algorithm", "Features"],
            last_title="Last model experiment",
            dashboard_titles=["OOS IC", "Model", "Gate", "Data"],
        )
        self._runtime = runtime
        self.refresh()

    def refresh(self) -> None:
        self.set_catalog_rows(
            [
                [
                    str(row["model_id"]),
                    str(row["algorithm"]),
                    str(row["features"]),
                ]
                for row in learning_catalog_rows()
            ]
        )
        last = last_learning_experiment_row(self._runtime)
        dash = self.dashboard
        if last is None:
            self.set_last_run(None)
            if dash is not None:
                for card in dash.cards:
                    card.set_value("—")
            return
        ic = last.get("oos_ic")
        if dash is not None:
            dash.card(0).set_value("" if ic is None else str(ic))
            dash.card(1).set_value(str(last.get("model_id", "—"))[:14])
            dash.card(2).set_value(str(last.get("gate_outcome", "—"))[:12])
            dash.card(3).set_value(str(last.get("data_kind", "—"))[:12])
        self.set_last_run(
            [
                ("experiment", str(last["id"])[:16]),
                ("model", str(last["model_id"])),
                ("algorithm", str(last["algorithm"])),
                ("gate", str(last["gate_outcome"])),
                ("data", str(last["data_kind"])),
                ("oos_ic", "" if last["oos_ic"] is None else str(last["oos_ic"])),
            ]
        )
