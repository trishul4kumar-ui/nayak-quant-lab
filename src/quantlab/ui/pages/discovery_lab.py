from __future__ import annotations

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.discovery import family_rows, last_discovery_experiment_row
from quantlab.ui.widgets.catalog_page import CatalogLabPage
from quantlab.ui.widgets.charts import BarChartWidget


class DiscoveryLabPage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Discovery Lab",
            subtitle="Generate and falsify expressions — not live alphas.",
            nayak_summary=(
                "Discovery proposes mathematical hypotheses from PIT features. "
                "A spectacular in-sample tree that fails OOS is a successful falsification. "
                "Synthetic results cannot promote."
            ),
            technical=(
                "Genetic search runs in quantlab.discovery via the CLI. "
                "This page is a query viewer. It does not evaluate expressions in Qt."
            ),
            catalog_title="Discovery families",
            catalog_headers=["Family", "Depth", "Pop", "Gens", "Note"],
            last_title="Last discovery search",
            empty_title="No discovery runs yet",
            empty_body="Run quantlab discovery search from the CLI. Results appear here.",
            empty_action=None,
            dashboard_titles=["Tested", "Novelty", "Gate", "Family"],
        )
        self._runtime = runtime
        self._bars = BarChartWidget()
        self.body().insertWidget(2, self._bars)
        self.refresh()

    def refresh(self) -> None:
        self.set_catalog_rows(
            [
                [
                    str(row["family_id"]),
                    str(row["max_depth"]),
                    str(row["population"]),
                    str(row["generations"]),
                    str(row["note"]),
                ]
                for row in family_rows()
            ]
        )
        last = last_discovery_experiment_row(self._runtime)
        dash = self.dashboard
        if last is None or dash is None:
            self.set_last_run(None)
            if dash is not None:
                for card in dash.cards:
                    card.set_value("—")
            self._bars.set_items([])
            return
        tested = last.get("tested_count")
        novelty = last.get("novelty")
        dash.card(0).set_value(str(tested) if tested is not None else "—")
        dash.card(1).set_value(str(novelty) if novelty is not None else "—")
        dash.card(2).set_value(str(last.get("gate_outcome", "—"))[:12])
        dash.card(3).set_value(str(last.get("family_id", "—"))[:12])
        bar_items: list[tuple[str, float, str]] = []
        if isinstance(tested, (int, float)):
            bar_items.append(("Tested", float(tested), "#42a5f5"))
        if isinstance(novelty, (int, float)):
            bar_items.append(("Novelty", float(novelty), "#66bb6a"))
        elif isinstance(novelty, str):
            try:
                bar_items.append(("Novelty", float(novelty), "#66bb6a"))
            except ValueError:
                pass
        self._bars.set_items(bar_items)
        self.set_last_run(
            [
                ("Ledger id", str(last["id"])),
                ("Family", str(last["family_id"])),
                ("Expression", str(last["expression_hash"])),
                ("Gate", str(last["gate_outcome"])),
                ("Data", str(last["data_kind"])),
                ("Tested", str(last["tested_count"])),
                ("Novelty", str(last["novelty"])),
                ("Identity", str(last["identity"])),
            ]
        )
