from __future__ import annotations

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.queries import ensemble_catalog_rows, last_ensemble_experiment_row
from quantlab.ui.widgets.catalog_page import CatalogLabPage


class EnsemblePage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Ensemble Lab",
            subtitle="Combine multiple signals with point-in-time weighting.",
            nayak_summary=(
                "Ensembles blend alphas or models into one score. "
                "Diversification can smooth noise — an ensemble is still not a portfolio."
            ),
            technical=(
                "PIT combination runs in the core; "
                "weights reflect only information available at decision time."
            ),
            catalog_title="Seed ensembles",
            catalog_headers=["Ensemble", "Weighting", "Method", "Components"],
            last_title="Last ensemble experiment",
            dashboard_titles=["OOS IC", "Ensemble", "Gate", "Data"],
        )
        self._runtime = runtime
        self.refresh()

    def refresh(self) -> None:
        self.set_catalog_rows(
            [
                [
                    str(row["ensemble_id"]),
                    str(row["weighting_policy"]),
                    str(row["combination_method"]),
                    str(row["components"]),
                ]
                for row in ensemble_catalog_rows()
            ]
        )
        last = last_ensemble_experiment_row(self._runtime)
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
            dash.card(1).set_value(str(last.get("ensemble_id", "—"))[:14])
            dash.card(2).set_value(str(last.get("gate_outcome", "—"))[:12])
            dash.card(3).set_value(str(last.get("data_kind", "—"))[:12])
        self.set_last_run(
            [
                ("experiment", str(last["id"])[:16]),
                ("ensemble", str(last["ensemble_id"])),
                ("weighting", str(last["weighting_policy"])),
                ("gate", str(last["gate_outcome"])),
                ("data", str(last["data_kind"])),
                ("oos_ic", "" if last["oos_ic"] is None else str(last["oos_ic"])),
            ]
        )
