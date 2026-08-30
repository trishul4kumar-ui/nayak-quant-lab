from __future__ import annotations

from PySide6.QtWidgets import QTableWidget

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.chart_data import experiment_scatter_points
from quantlab.app.queries import experiment_rows
from quantlab.ui.widgets import fill_table
from quantlab.ui.widgets.charts import DashboardStrip, ScatterChartWidget
from quantlab.ui.widgets.lab_shell import LabPageShell


class ExperimentsPage(LabPageShell):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Experiment ledger",
            subtitle="Every backtest and validation run — double-click an ID to open Journal.",
            nayak_summary=(
                "The ledger is append-only research memory. "
                "Synthetic Sharpe teaches mechanics, not live edge."
            ),
        )
        self._runtime = runtime
        body = self.body()
        self._dash = DashboardStrip(["Runs", "Avg Sharpe", "Pass rate", "Latest gate"])
        body.addWidget(self._dash)
        self._scatter = ScatterChartWidget()
        body.addWidget(self._scatter)
        self._table = QTableWidget()
        body.addWidget(self._table, 1)
        self.refresh()

    def refresh(self) -> None:
        rows_data = experiment_rows(self._runtime)
        points = experiment_scatter_points(self._runtime)
        self._scatter.set_points(
            [(p["x"], p["y"], p["name"]) for p in points],
            x_label="Sharpe",
            y_label="Total return",
        )

        n = len(rows_data)
        sharpes = [r["sharpe"] for r in rows_data if isinstance(r.get("sharpe"), float)]
        avg_sh = sum(sharpes) / len(sharpes) if sharpes else None
        gates = [str(r.get("gate_outcome") or "") for r in rows_data]
        pass_n = sum(1 for g in gates if g.lower() == "pass")
        pass_rate = pass_n / n if n else 0.0
        latest_gate = gates[0] if gates else "—"

        self._dash.card(0).set_value(str(n), accent="#42a5f5")
        self._dash.card(1).set_value(f"{avg_sh:.2f}" if avg_sh is not None else "—")
        self._dash.card(2).set_value(f"{pass_rate:.0%}" if n else "—", accent="#66bb6a")
        self._dash.card(3).set_value(latest_gate[:12] or "—")

        rows = []
        links: dict[tuple[int, int], str] = {}
        for r, row in enumerate(rows_data):
            exp_id = str(row["id"])
            links[(r, 0)] = exp_id
            rows.append(
                [
                    exp_id[:12],
                    str(row["name"]),
                    str(row["status"]),
                    "" if row["sharpe"] is None else f"{row['sharpe']:.3f}",
                    str(row["genome_id"]),
                    str(row["data_kind"]),
                    str(row.get("gate_outcome") or ""),
                    str(row["version"]),
                ]
            )
        fill_table(
            self._table,
            ["Id", "Name", "Status", "Sharpe", "Genome", "Kind", "Gate", "App"],
            rows,
            experiment_links=links,
        )
