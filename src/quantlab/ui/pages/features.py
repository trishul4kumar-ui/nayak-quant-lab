from __future__ import annotations

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.queries import feature_catalog_rows, last_feature_experiment_row
from quantlab.ui.widgets.catalog_page import CatalogLabPage
from quantlab.ui.widgets.charts import BarChartWidget


class FeaturesPage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Features",
            subtitle="Versioned inputs to every model and alpha in the lab.",
            nayak_summary=(
                "Features are measurable properties of price and volume history. "
                "A feature with no predictive power is still a valid research result."
            ),
            technical=(
                "Definitions are versioned and point-in-time safe; "
                "computation runs in the core pipeline."
            ),
            catalog_title="Feature catalog",
            catalog_headers=["Feature", "Version", "Family", "Lookback", "Lifecycle", "Identity"],
            last_title="Last feature experiment",
            empty_body="Run a feature experiment from the CLI or pipeline — IC appears here.",
            dashboard_titles=["Spearman IC", "Feature", "Gate", "Label"],
        )
        self._runtime = runtime
        self._ic_chart = BarChartWidget()
        self.body().insertWidget(2, self._ic_chart)
        self.refresh()

    def refresh(self) -> None:
        rows = [
            [
                str(row["feature_id"]),
                str(row["version"]),
                str(row["family"]),
                str(row["lookback"]),
                str(row["lifecycle"]),
                str(row["identity"])[:12],
            ]
            for row in feature_catalog_rows()
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
        dash.card(0).set_value(
            f"{ic:.3f}" if isinstance(ic, float) else "—",
            accent="#42a5f5",
        )
        dash.card(1).set_value(str(found.get("feature_id", "—"))[:14])
        dash.card(2).set_value(str(found.get("gate_outcome", "—"))[:12])
        dash.card(3).set_value(str(found.get("label", "—"))[:14])
        bar_items: list[tuple[str, float, str]] = []
        if isinstance(ic, float):
            bar_items.append(("Spearman IC", ic, "#42a5f5"))
        ic_n = found.get("ic_n")
        if isinstance(ic_n, (int, float)):
            bar_items.append(("IC n", float(ic_n), "#66bb6a"))
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
