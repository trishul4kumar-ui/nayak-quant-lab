from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
)

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.chart_data import (
    BENCHMARK_COLOR,
    BENCHMARK_LABEL,
    equity_for_experiments,
    rebase_to_one,
)
from quantlab.app.copy import SYNTHETIC_SHARPE_DISCLAIMER
from quantlab.app.queries import experiment_rows
from quantlab.ui.widgets.charts import (
    SERIES_COLORS,
    ChartSeries,
    DashboardStrip,
    MultiSeriesChartWidget,
)
from quantlab.ui.widgets.data_table import fill_table
from quantlab.ui.widgets.lab_shell import LabPageShell


class ComparePage(LabPageShell):
    """Pick up to three experiments and compare metrics side by side."""

    MAX_SELECTED = 3

    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Compare",
            subtitle="Overlay rebased equity curves and metrics for up to three runs.",
            nayak_summary=(
                f"Curves start at 1.0 so different capital scales compare fairly. "
                f"Dashed gray is the cash benchmark. {SYNTHETIC_SHARPE_DISCLAIMER}"
            ),
        )
        self._runtime = runtime
        self._rows: list[dict[str, Any]] = []
        self._updating_selection = False
        body = self.body()

        self._dash = DashboardStrip(["Selected", "Avg Sharpe", "With equity", "Benchmark"])
        body.addWidget(self._dash)

        picker_row = QHBoxLayout()
        self._picker = QListWidget()
        self._picker.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self._picker.itemSelectionChanged.connect(self._on_selection_changed)
        picker_row.addWidget(self._picker, 1)

        actions = QVBoxLayout()
        self._compare_btn = QPushButton("Compare selected")
        self._compare_btn.setObjectName("primary")
        self._compare_btn.setEnabled(False)
        self._compare_btn.setToolTip("Select at least one experiment to compare")
        self._compare_btn.clicked.connect(self._render_selected)
        self._select_latest = QPushButton("Latest 3")
        self._select_latest.clicked.connect(self._select_latest_three)
        actions.addWidget(self._compare_btn)
        actions.addWidget(self._select_latest)
        actions.addStretch()
        picker_row.addLayout(actions)
        body.addLayout(picker_row)

        self._hint = QLabel()
        self._hint.setObjectName("nayakVoice")
        body.addWidget(self._hint)

        self._legend = QLabel("Legend follows run colors · dashed line = cash benchmark")
        self._legend.setObjectName("nayakVoice")
        body.addWidget(self._legend)

        self._curve_chart = MultiSeriesChartWidget()
        self._curve_chart.set_empty_message("No equity artifact — run a backtest first")
        body.addWidget(self._curve_chart)

        self._table = QTableWidget()
        body.addWidget(self._table, 1)
        self.refresh()

    def refresh(self) -> None:
        self._rows = experiment_rows(self._runtime)[:12]
        self._picker.blockSignals(True)
        self._picker.clear()
        for i, row in enumerate(self._rows):
            sharpe = row.get("sharpe")
            sharpe_txt = f"{sharpe:.2f}" if isinstance(sharpe, float) else "—"
            label = f"{row['name']} — Sharpe {sharpe_txt} · {row.get('data_kind', 'synthetic')}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, row["id"])
            color = SERIES_COLORS[i % len(SERIES_COLORS)]
            item.setForeground(QColor(color))
            self._picker.addItem(item)
        self._picker.blockSignals(False)
        self._select_latest_three()

    def _select_latest_three(self) -> None:
        self._updating_selection = True
        self._picker.clearSelection()
        for index in range(min(self.MAX_SELECTED, self._picker.count())):
            item = self._picker.item(index)
            if item is not None:
                item.setSelected(True)
        self._updating_selection = False
        self._render_selected()

    def _on_selection_changed(self) -> None:
        if self._updating_selection:
            return
        selected = self._picker.selectedItems()
        if len(selected) > self.MAX_SELECTED:
            self._updating_selection = True
            for item in selected[self.MAX_SELECTED :]:
                item.setSelected(False)
            self._updating_selection = False
            selected = self._picker.selectedItems()
        count = len(selected)
        self._compare_btn.setEnabled(count >= 1)
        self._hint.setText(
            f"{count} selected (max {self.MAX_SELECTED}). "
            + ("Choose at least one run to compare." if count == 0 else "")
        )
        if count >= 1:
            self._render_selected()

    def _selected_rows(self) -> list[dict[str, Any]]:
        ids = [str(item.data(Qt.ItemDataRole.UserRole)) for item in self._picker.selectedItems()]
        by_id = {str(row["id"]): row for row in self._rows}
        return [by_id[run_id] for run_id in ids if run_id in by_id]

    def _render_selected(self) -> None:
        rows = self._selected_rows()
        self._compare_btn.setEnabled(bool(rows))
        if not rows:
            fill_table(self._table, ["Metric"], [["Select runs from the list above"]])
            self._curve_chart.set_series([])
            for card in self._dash.cards:
                card.set_value("—")
            return

        ids = [str(row["id"]) for row in rows]
        curves = equity_for_experiments(self._runtime, ids)
        series: list[ChartSeries] = []
        with_equity = 0
        sharpes: list[float] = []
        max_len = 0
        for i, row in enumerate(rows):
            exp_id = str(row["id"])
            values = curves.get(exp_id, [])
            sharpe = row.get("sharpe")
            if isinstance(sharpe, float):
                sharpes.append(sharpe)
            if len(values) >= 2:
                with_equity += 1
                max_len = max(max_len, len(values))
                series.append(
                    ChartSeries(
                        label=str(row["name"])[:16],
                        values=rebase_to_one(values),
                        color=SERIES_COLORS[i % len(SERIES_COLORS)],
                    )
                )
        if max_len >= 2:
            series.append(
                ChartSeries(
                    label=BENCHMARK_LABEL,
                    values=[1.0] * max_len,
                    color=BENCHMARK_COLOR,
                    dashed=True,
                )
            )
        self._curve_chart.set_series(series)
        if with_equity == 0:
            self._curve_chart.set_empty_message("No equity artifact — run a backtest first")

        avg_sharpe = sum(sharpes) / len(sharpes) if sharpes else None
        self._dash.card(0).set_value(str(len(rows)))
        self._dash.card(1).set_value(
            f"{avg_sharpe:.2f}" if avg_sharpe is not None else "—",
            accent="#42a5f5",
        )
        self._dash.card(2).set_value(f"{with_equity}/{len(rows)}")
        self._dash.card(3).set_value("Cash" if with_equity else "—")

        headers = ["Metric"] + [str(row["name"])[:22] for row in rows]
        metric_keys = [
            ("Sharpe", "sharpe", ".2f"),
            ("Total return", "total_return", ".4f"),
            ("Max drawdown", "max_drawdown", ".2%"),
            ("Data kind", "data_kind", "s"),
            ("Gate", "gate_outcome", "s"),
            ("Status", "status", "s"),
            ("Experiment", "id", "s"),
        ]
        body: list[list[str]] = []
        links: dict[tuple[int, int], str] = {}
        for r, (label, key, fmt) in enumerate(metric_keys):
            cells = [label]
            for c, row in enumerate(rows):
                value = row.get(key)
                if key == "id" and value:
                    links[(r, c + 1)] = str(value)
                if value is None:
                    cells.append("—")
                elif fmt == "s":
                    cells.append(str(value)[:16])
                elif fmt == ".2%":
                    cells.append(f"{value:.2%}" if isinstance(value, float) else str(value))
                elif isinstance(value, float):
                    cells.append(f"{value:{fmt}}")
                else:
                    cells.append(str(value))
            body.append(cells)
        fill_table(self._table, headers, body, experiment_links=links)
        self._hint.setText(
            f"Comparing {len(rows)} run(s)"
            + (" · some runs lack equity artifacts" if with_equity < len(rows) else "")
            + "."
        )
