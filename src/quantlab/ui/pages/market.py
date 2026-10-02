from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QTableWidget

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.queries import (
    last_cross_section_state_row,
    last_regime_experiment_row,
    market_close_series,
    market_rows,
    regime_catalog_rows,
)
from quantlab.app.settings_store import ExperienceMode
from quantlab.ui.widgets import (
    ExplainChip,
    TerminalGrid,
    TerminalPanel,
    WatchlistWidget,
    fill_table,
)
from quantlab.ui.widgets.charts import SparklineWidget
from quantlab.ui.widgets.lab_shell import LabPageShell


class MarketPage(LabPageShell):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Market Lab",
            subtitle="Synthetic NSE-style universe — not a live feed.",
            nayak_summary=(
                "Interactive terminal view. Click a watchlist row to inspect an instrument. "
                "NAYAK labels are descriptive, not forecasts."
            ),
        )
        self._runtime = runtime
        self._market_data: list[dict[str, Any]] = []
        self.add_toolbar_widget(ExplainChip("regime", label="Regime"))

        body = self.body()
        self._watchlist = WatchlistWidget()
        self._watchlist.instrument_selected.connect(self._show_instrument)
        self._price_spark = SparklineWidget(min_height=120)
        self._detail = QTableWidget()
        self._snapshot = QTableWidget()
        self._models = QTableWidget()
        self._last_regime = QTableWidget()

        cols = 1 if runtime.ui_settings.current.experience_mode is ExperienceMode.GUIDED else 2
        self._terminal = TerminalGrid(
            columns=cols,
            layout_id="market",
            settings=runtime.ui_settings,
        )
        self._terminal.set_panels(
            [
                TerminalPanel("Watchlist", self._watchlist, explain_key="momentum_20"),
                TerminalPanel("Price trend", self._price_spark, explain_key="close"),
                TerminalPanel("Instrument", self._detail, explain_key="close"),
                TerminalPanel("Universe snapshot", self._snapshot, explain_key="regime"),
                TerminalPanel("Regime catalog", self._models, explain_key="regime"),
            ]
        )
        body.addWidget(self._terminal, 1)
        body.addWidget(ExplainChip("gate_outcome", label="Last regime run"))
        body.addWidget(self._last_regime)
        self.refresh()

    @property
    def models(self) -> QTableWidget:
        return self._models

    def _show_instrument(self, row: dict[str, Any]) -> None:
        inst = str(row["instrument"])
        closes = market_close_series(inst)
        if len(closes) >= 2:
            color = "#66bb6a" if closes[-1] >= closes[0] else "#ef5350"
            self._price_spark.set_values(closes, color=color)
        else:
            self._price_spark.set_values([])
        mom = row.get("momentum_20")
        mom_txt = "" if mom is None else f"{mom:.4f}"
        fill_table(
            self._detail,
            ["Field", "Value"],
            [
                ["Instrument", str(row["instrument"])],
                ["Name", str(row.get("name", ""))],
                ["Close ₹", f"{row['close']:.2f}"],
                ["Volume", f"{row['volume']:.0f}"],
                ["Momentum 20", mom_txt],
                ["As of", str(row["as_of"])],
            ],
        )

    def refresh(self) -> None:
        self._market_data = market_rows()
        self._watchlist.set_market_rows(self._market_data)
        if self._market_data:
            self._show_instrument(self._market_data[0])

        found = last_cross_section_state_row()
        if found is None:
            fill_table(self._snapshot, ["Field", "Value"], [["status", "no snapshot"]])
        else:
            fill_table(
                self._snapshot,
                ["Field", "Value"],
                [[key, "" if value is None else str(value)] for key, value in found.items()],
            )

        fill_table(
            self._models,
            ["Model", "Detector", "N", "Lifecycle", "Identity"],
            [
                [
                    str(row["regime_model_id"]),
                    str(row["detector"]),
                    str(row["n_regimes"]),
                    str(row["lifecycle"]),
                    str(row["identity"])[:12],
                ]
                for row in regime_catalog_rows()
            ],
        )

        last = last_regime_experiment_row(self._runtime)
        if last is None:
            fill_table(
                self._last_regime,
                ["Field", "Value"],
                [["status", "no regime experiments yet"]],
            )
            return
        fill_table(
            self._last_regime,
            ["Field", "Value"],
            [
                ["experiment", str(last["id"])],
                ["regime_model_id", str(last["regime_model_id"])],
                ["gate", str(last["gate_outcome"])],
                ["data_kind", str(last["data_kind"])],
                [
                    "n_labelled",
                    "" if last["n_labelled"] is None else str(last["n_labelled"]),
                ],
            ],
            experiment_links={(0, 1): str(last["id"])},
        )

    def save_terminal_layout(self) -> None:
        self._terminal.persist_layout()
