from __future__ import annotations

from typing import Any

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel, QPushButton, QTableWidget

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.live_market import display_time
from quantlab.app.queries import (
    last_regime_experiment_row,
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
from quantlab.ui.widgets.data_table import update_table_values
from quantlab.ui.widgets.lab_shell import LabPageShell
from quantlab.ui.widgets.market_chart import MarketChartWorkspace


class MarketPage(LabPageShell):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Market Lab",
            subtitle="Kite market quotes · observe-only · automatic 2-second REST refresh.",
            nayak_summary=(
                "Connect Kite to view your configured instruments. Quote timestamps and ages "
                "come from the provider; no synthetic fallback. Select an instrument for "
                "historical candles or observed quotes, and Expand for the full chart workspace. "
                "Market data access does not enable live trading."
            ),
        )
        self._runtime = runtime
        self._market_data: list[dict[str, Any]] = []
        self._feed_state = QLabel("Kite · DISCONNECTED")
        self.add_toolbar_widget(self._feed_state)
        self._connect = QPushButton("Connect Kite")
        self._connect.setObjectName("primary")
        self._connect.clicked.connect(self._connect_feed)
        self.add_toolbar_widget(self._connect)
        self._refresh = QPushButton("Refresh quotes")
        self._refresh.clicked.connect(self._refresh_feed)
        self.add_toolbar_widget(self._refresh)
        self._pause = QPushButton("Pause feed")
        self._pause.clicked.connect(self._pause_feed)
        self.add_toolbar_widget(self._pause)
        self._message = QLabel()
        self._message.setWordWrap(True)

        body = self.body()
        self._watchlist = WatchlistWidget()
        self._watchlist.instrument_selected.connect(self._show_instrument)
        body.addWidget(self._message)
        self._price_spark = MarketChartWorkspace(runtime)
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
                TerminalPanel("Kite watchlist · LTP / depth", self._watchlist),
                TerminalPanel("Interactive market chart · IST", self._price_spark),
                TerminalPanel("Instrument", self._detail, explain_key="close"),
                TerminalPanel("Feed provenance / health", self._snapshot),
                TerminalPanel(
                    "Research regime catalog · not live signals", self._models, explain_key="regime"
                ),
            ]
        )
        body.addWidget(self._terminal, 1)
        body.addWidget(ExplainChip("gate_outcome", label="Last regime run"))
        body.addWidget(self._last_regime)
        self.refresh()
        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._poll_feed)
        self._timer.start()

    @property
    def models(self) -> QTableWidget:
        return self._models

    def _show_instrument(self, row: dict[str, Any]) -> None:
        inst = str(row["instrument"])
        self._price_spark.set_instrument(
            inst, quote=row, observed=self._runtime.live_market.history(inst)
        )

        def number(key: str) -> str:
            value = row.get(key)
            return "—" if value is None else f"{value:,.2f}"

        update_table_values(
            self._detail,
            ["Field", "Value"],
            [
                ["Instrument", str(row["instrument"])],
                ["LTP / value (provider units)", number("price")],
                ["Bid / Ask", f"{number('bid')} / {number('ask')}"],
                ["Volume", number("volume")],
                ["Provider quote time", display_time(row.get("quote_time"))],
                ["Received", display_time(row.get("receive_time"))],
                ["Quality now", str(row["quality"])],
                ["Source", str(row["source"])],
                ["Momentum / regime", "Unavailable without validated real historical data"],
            ],
        )

    def _connect_feed(self) -> None:
        self._runtime.live_market.start()
        self._render_feed()

    def _refresh_feed(self) -> None:
        self._runtime.live_market.refresh_now()
        self._render_feed()

    def _pause_feed(self) -> None:
        self._runtime.live_market.pause()
        self._render_feed()

    def _poll_feed(self) -> None:
        if self._runtime.is_closed:
            self._timer.stop()
            return
        self._runtime.live_market.tick()
        if self.isVisible() or self._price_spark.is_expanded:
            self._render_feed()

    def _render_feed(self) -> None:
        feed = self._runtime.live_market
        self._feed_state.setText(f"Kite · {feed.status}")
        self._connect.setText(
            "Connected"
            if feed.enabled and feed.snapshot and not feed.error
            else "Reconnect Kite"
            if feed.error
            else "Connect Kite"
        )
        self._connect.setToolTip("Quotes are observe-only. Use Refresh quotes or Pause feed.")
        self._connect.setEnabled(not feed.busy and not feed.enabled)
        self._refresh.setEnabled(not feed.busy and feed.enabled)
        self._pause.setEnabled(feed.enabled)
        if feed.error:
            message = feed.error + ". No synthetic fallback; retained quotes are unavailable."
            if "authentication rejected" in feed.error:
                message += (
                    " Run python -m quantlab.cli market-data kite-login, then Reconnect Kite."
                )
        elif not feed.enabled:
            message = (
                "Feed paused." if feed.snapshot else "Click Connect Kite to fetch real quotes."
            )
        else:
            message = (
                "Updating in the background · GET /quote · no orders or tick-stream guarantee."
            )
            if feed.snapshot:
                message += f" Last capture: {display_time(feed.snapshot.as_of)}."
                message += (
                    f" {feed.snapshot.n_names} instruments · provider-native price / index / "
                    "yield units. Indices may have no depth or volume; global quotes can be older."
                )
        self._message.setText(message)
        self._market_data = feed.quote_rows()
        self._watchlist.set_quote_rows(self._market_data)
        if not self._market_data:
            update_table_values(
                self._detail, ["Field", "Value"], [["Status", "No Kite quotes yet"]]
            )
        frozen = feed.snapshot
        update_table_values(
            self._snapshot,
            ["Field", "Value"],
            [
                ["Status now", feed.status],
                ["Source", "kite-rest-quote-v3 · REST polling, not WebSocket ticks"],
                ["Indian weekday session", frozen.session.value if frozen else "unknown"],
                ["Received snapshot", display_time(frozen.as_of) if frozen else "—"],
                [
                    "Instrument coverage",
                    str(frozen.extras.get("coverage", "unknown")) if frozen else "—",
                ],
                [
                    "Provider faults",
                    str(frozen.extras.get("quality_faults", ())) if frozen else "—",
                ],
                [
                    "Quote age limit",
                    f"{frozen.extras.get('max_quote_age_seconds', 5)}s" if frozen else "—",
                ],
                ["Calendar", "weekday-v1 · no verified holiday or global-session calendar"],
                ["Live trading / broker writes", "DISABLED / DISABLED"],
            ],
        )

    def refresh(self) -> None:
        self._render_feed()

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
