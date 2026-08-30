from __future__ import annotations

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.queries import alpha_catalog_rows, last_feature_experiment_row
from quantlab.ui.widgets.catalog_page import CatalogLabPage
from quantlab.ui.widgets.charts import BarChartWidget


class AlphaPage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Alpha Lab",
            subtitle="Transform features into ranked signals — research only, no live orders.",
            nayak_summary=(
                "Alphas turn features into tradeable rankings. IC and decay tell you "
                "whether a signal is real on synthetic data — not whether it will work live."
            ),
            technical=(
                "Seed catalog from the research ledger. Promotion requires validation gate pass."
            ),
            catalog_title="Seed alphas",
            catalog_headers=["Alpha", "Inputs", "Transform", "Horizon", "Lifecycle"],
            last_title="Last alpha experiment",
            empty_body="Run a feature or alpha experiment — your latest result appears here.",
            dashboard_titles=["Spearman IC", "IC n", "Gate", "Data kind"],
        )
        self._runtime = runtime
        self._ic_chart = BarChartWidget()
        self.body().insertWidget(2, self._ic_chart)
        self.refresh()

    def refresh(self) -> None:
        rows = [
            [
                str(row["alpha_id"]),
                str(row["inputs"]),
                str(row["transformation"]),
                str(row["horizon"]),
                str(row["lifecycle"]),
            ]
            for row in alpha_catalog_rows()
        ]
        self.set_catalog_rows(rows)
        found = last_feature_experiment_row(self._runtime)
        dash = self.dashboard
        if found is None or dash is None:
            self.set_last_run(None)
            if dash is not None:
                for card in dash.cards:
                    card.set_value("—")
            self._ic_chart.set_items([])
            return
        ic = found["spearman_ic"]
        ic_n = found.get("ic_n")
        dash.card(0).set_value(
            f"{ic:.3f}" if isinstance(ic, float) else "—",
            accent="#42a5f5",
        )
        dash.card(1).set_value(str(ic_n) if ic_n is not None else "—")
        dash.card(2).set_value(str(found.get("gate_outcome", "—"))[:12])
        dash.card(3).set_value(str(found.get("data_kind", "—"))[:12])
        bar_items: list[tuple[str, float, str]] = []
        if isinstance(ic, float):
            bar_items.append(("IC", ic, "#42a5f5"))
        if isinstance(ic_n, (int, float)):
            bar_items.append(("n", float(ic_n), "#66bb6a"))
        self._ic_chart.set_items(bar_items)
        self.set_last_run(
            [
                ("experiment", str(found["id"])[:16]),
                ("feature", str(found["feature_id"])),
                ("gate", str(found["gate_outcome"])),
                ("data", str(found["data_kind"])),
                ("label", str(found["label"])),
                ("spearman_ic", "" if ic is None else f"{ic:.4f}"),
                ("n", "" if ic_n is None else str(ic_n)),
            ]
        )
