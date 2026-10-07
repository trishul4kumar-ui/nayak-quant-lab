"""Interactive native Kite chart workspace. Display tools cannot submit orders."""

from __future__ import annotations

import csv
from typing import Any

from PySide6.QtCore import QEvent, QTimer
from PySide6.QtGui import QAction, QResizeEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QMenu,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.live_market import QuotePoint, display_time
from quantlab.realtime_data.candles import ChartRequest
from quantlab.ui.widgets.interactive_chart import InteractivePriceChart

TIMEFRAMES = [
    ("1m", "minute"),
    ("3m", "3minute"),
    ("5m", "5minute"),
    ("10m", "10minute"),
    ("15m", "15minute"),
    ("30m", "30minute"),
    ("1h", "60minute"),
    ("1D", "day"),
    ("Observed quotes", "observed"),
]


class MarketChartWorkspace(QWidget):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__()
        self._runtime = runtime
        self._quote: dict[str, Any] = {}
        self._observed: list[QuotePoint] = []
        self._instrument = ""
        self._revision = -1
        self._expanded: QDialog | None = None
        self.setAccessibleName(
            "Market chart in provider units with timeframe and indicator controls"
        )
        self._root = QVBoxLayout(self)
        # Manage height-for-width explicitly: Qt's ordinary minimumSize() omits
        # wrapped label height, which can overlap a canvas inside a splitter.
        self._root.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self._root.setContentsMargins(0, 0, 0, 0)
        self._root.setSpacing(6)
        self._headline = QLabel("Select a watchlist instrument")
        self._headline.setWordWrap(True)
        self._root.addWidget(self._headline)
        self._controls = QGridLayout()
        self._controls.setContentsMargins(0, 0, 0, 0)
        self._root.addLayout(self._controls)
        self._timeframe = QComboBox()
        self._timeframe.setAccessibleName("Candle timeframe")
        self._timeframe.setToolTip(
            "Kite historical candles start at 1 minute. Observed quotes are samples, not OHLC."
        )
        for label, value in TIMEFRAMES:
            self._timeframe.addItem(label, value)
        self._range = QComboBox()
        self._range.setAccessibleName("Chart history range")
        for label, days in (("Today", 1), ("5 days", 5), ("1 month", 31), ("1 year · daily", 366)):
            self._range.addItem(label, days)
        self._range.setCurrentIndex(1)
        self._view = QComboBox()
        self._view.setAccessibleName("Chart view")
        self._view.addItems(["Candles", "OHLC", "Line", "Area"])
        self._indicators = QToolButton()
        self._indicators.setText("Indicators")
        self._indicators.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(self._indicators)
        self._indicator_actions: dict[str, QAction] = {}
        definitions = {
            "SMA 20": "Arithmetic mean of 20 candle closes; 19-bar warm-up.",
            "EMA 9": "9-close EMA; SMA seed, alpha=2/10.",
            "EMA 26": "26-close EMA; SMA seed, alpha=2/27.",
            "BB 20": "20-close SMA +/- 2 population standard deviations.",
            "RSI 14": "14-period Wilder RSI; 0–100, flat prices=50.",
        }
        for name, definition in definitions.items():
            action = menu.addAction(name)
            action.setCheckable(True)
            action.setChecked(name in {"EMA 9", "EMA 26"})
            action.setToolTip(definition + " Display only; not a trade signal.")
            action.toggled.connect(lambda checked, n=name: self._indicator_changed(n, checked))
            self._indicator_actions[name] = action
        self._indicators.setMenu(menu)
        self._volume = QCheckBox("Volume")
        self._volume.setChecked(True)
        self._auto = QCheckBox("Auto · 20s")
        self._auto.setChecked(True)
        self._auto.setToolTip(
            "Refresh provider candles every 20 seconds; quote marker updates separately"
        )
        self._tool = QComboBox()
        self._tool.setAccessibleName("Chart drawing tool")
        self._tool.addItems(["Crosshair", "Horizontal", "Trend line"])
        self._tool.setToolTip(
            "Trend line: click two endpoints. Drawings are local notes, not orders."
        )
        for combo in (self._timeframe, self._range, self._view, self._tool):
            combo.setSizeAdjustPolicy(
                QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
            )
            combo.setMinimumContentsLength(5)
            combo.setMinimumWidth(0)
            combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._canvas = InteractivePriceChart()
        self._readout = QLabel("Hover a bar for OHLC and volume · arrows also inspect")
        self._readout.setWordWrap(True)
        self._canvas.inspected.connect(self._readout.setText)
        self._follow = QPushButton("Latest")
        self._follow.setCheckable(True)
        self._follow.setChecked(True)
        self._follow.clicked.connect(self._latest)
        self._canvas.navigation_changed.connect(self._follow.setChecked)
        self._fit = QPushButton("Fit")
        self._fit.clicked.connect(self._canvas.fit)
        self._zoom_in = QPushButton("+")
        self._zoom_in.setToolTip("Zoom in")
        self._zoom_in.clicked.connect(lambda: self._canvas.zoom(0.8))
        self._zoom_out = QPushButton("−")
        self._zoom_out.setToolTip("Zoom out")
        self._zoom_out.clicked.connect(lambda: self._canvas.zoom(1.25))
        self._undo = QPushButton("Undo")
        self._undo.clicked.connect(self._undo_drawing)
        self._clear = QPushButton("Clear")
        self._clear.setToolTip("Clear local drawings only")
        self._clear.clicked.connect(self._clear_drawings)
        self._canvas.drawings_changed.connect(self._update_drawing_buttons)
        self._update_drawing_buttons()
        self._refresh = QPushButton("Reload")
        self._refresh.clicked.connect(self._reload)
        self._expand = QPushButton("Expand")
        self._expand.clicked.connect(self._expand_chart)
        self._png = QPushButton("PNG")
        self._png.clicked.connect(self._export_png)
        self._csv = QPushButton("CSV")
        self._csv.clicked.connect(self._export_csv)
        self._groups = [
            self._group(self._timeframe, self._range, self._view),
            self._group(self._indicators, self._volume, self._auto),
            self._group(self._zoom_in, self._zoom_out, self._fit, self._follow),
            self._group(self._tool, self._undo, self._clear),
            self._group(self._refresh, self._expand, self._png, self._csv),
        ]
        self._columns = 0
        self._arrange(700)
        self._root.addWidget(self._readout)
        self._legend = QLabel("EMA 9 · EMA 26 · candle-close indicators, not trade signals")
        self._legend.setWordWrap(True)
        self._root.addWidget(self._legend)
        self._root.addWidget(self._canvas, 1)
        self._status = QLabel("Historical candles: waiting for Kite connection")
        self._status.setWordWrap(True)
        self._root.addWidget(self._status)
        self._timeframe.currentIndexChanged.connect(self._selection_changed)
        self._range.currentIndexChanged.connect(self._selection_changed)
        self._view.currentTextChanged.connect(self._view_changed)
        self._tool.currentTextChanged.connect(self._tool_changed)
        self._volume.toggled.connect(self._volume_changed)
        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._poll)
        self._timer.start()

    @property
    def is_expanded(self) -> bool:
        return self._expanded is not None

    @staticmethod
    def _group(*widgets: QWidget) -> QWidget:
        group = QWidget()
        # Ignore the two-column minimum so a resize can cross the reflow breakpoint.
        group.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        layout = QHBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        for widget in widgets:
            layout.addWidget(widget)
        return group

    def _arrange(self, width: int) -> None:
        columns = 1 if width < 650 else 2
        if columns == self._columns:
            return
        self._columns = columns
        for i, group in enumerate(self._groups):
            self._controls.removeWidget(group)
            self._controls.addWidget(group, i // columns, i % columns)

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        self._arrange(self.width())
        self._sync_minimum_height()
        super().resizeEvent(event)

    def event(self, event: QEvent) -> bool:
        handled = super().event(event)
        if event.type() == QEvent.Type.LayoutRequest and hasattr(self, "_root"):
            self._sync_minimum_height()
        return handled

    def _sync_minimum_height(self) -> None:
        height = max(
            self._root.minimumSize().height(), self._root.minimumHeightForWidth(self.width())
        )
        if height > 0 and height != self.minimumHeight():
            self.setMinimumHeight(height)

    def set_instrument(
        self, instrument: str, *, quote: dict[str, Any], observed: list[QuotePoint]
    ) -> None:
        changed = instrument != self._instrument
        self._instrument, self._quote, self._observed = instrument, quote, list(observed)
        if changed:
            self._canvas.drawings.clear()
            self._readout.setText("Hover a bar for OHLC and volume · arrows also inspect")
            self._selection_changed()
        price = quote.get("price")
        quality = str(quote.get("quality", "missing"))
        self._headline.setText(
            f"{instrument} · Quote {price:,.2f} · {quality} · "
            f"{display_time(quote.get('quote_time'))}"
            if price is not None
            else f"{instrument} · quote unavailable"
        )
        self._canvas.live_price, self._canvas.live_quality = price, quality
        if self._timeframe.currentData() == "observed":
            self._canvas.set_series(instrument, None, observed)
        self._canvas.update()

    def _selection_changed(self, *_args: object) -> None:
        observed = self._timeframe.currentData() == "observed"
        self._indicators.setEnabled(not observed)
        self._volume.setEnabled(not observed)
        self._range.setEnabled(not observed)
        self._auto.setEnabled(not observed)
        if observed:
            if self._view.currentText() not in {"Line", "Area"}:
                self._view.setCurrentText("Line")
            self._canvas.set_series(self._instrument, None, self._observed)
            self._canvas._empty = "No fresh quote samples in this app session yet"
            self._status.setText(
                "Observed REST quotes only · elapsed-time axis · no reconstructed OHLC"
            )
            self._readout.setText("Hover a sample for its provider timestamp and observed LTP")
            self._update_legend()
            self._poll()
            return
        if self._timeframe.currentData() != "day" and self._range.currentData() == 366:
            if self.sender() is self._range:
                self._timeframe.blockSignals(True)
                self._timeframe.setCurrentIndex(self._timeframe.findData("day"))
                self._timeframe.blockSignals(False)
            else:
                self._range.blockSignals(True)
                self._range.setCurrentIndex(2)
                self._range.blockSignals(False)
        if not self._instrument:
            return
        request = ChartRequest(
            self._instrument, str(self._timeframe.currentData()), int(self._range.currentData())
        )
        self._runtime.chart_data.select(request)
        self._canvas.drawings.clear()
        self._canvas._pending_draw = None
        self._update_drawing_buttons()
        self._canvas.follow = True
        self._canvas.set_series(self._instrument, None)
        self._canvas._empty = (
            "Loading provider candles when Kite is connected · no synthetic fallback"
        )
        self._readout.setText("Hover a bar for OHLC and volume · arrows also inspect")
        self._update_legend()
        self._revision = -1
        self._poll()

    def _view_changed(self, text: str) -> None:
        if self._timeframe.currentData() == "observed" and text in {"Candles", "OHLC"}:
            self._view.setCurrentText("Line")
            return
        self._canvas.view = text
        self._canvas.update()

    def _indicator_changed(self, name: str, enabled: bool) -> None:
        if enabled:
            self._canvas.indicators.add(name)
        else:
            self._canvas.indicators.discard(name)
        self._canvas.update()
        self._update_legend()

    def _update_legend(self) -> None:
        if self._timeframe.currentData() == "observed":
            self._legend.setText("Observed quote samples · candle indicators unavailable")
            return
        colors = {
            "SMA 20": "#c4a76b",
            "EMA 9": "#42a5f5",
            "EMA 26": "#8bc34a",
            "BB 20": "#9575cd",
            "RSI 14": "#9575cd",
        }
        labels: list[str] = []
        for name, color in colors.items():
            if name not in self._canvas.indicators:
                continue
            values = self._canvas._rsi if name == "RSI 14" else self._canvas._overlays.get(name, [])
            value = values[-1] if values else None
            label = "±2σ" if name == "BB 20" else "—" if value is None else f"{value:,.2f}"
            labels.append(f'<span style="color:{color}">{name} {label}</span>')
        self._legend.setText(
            " · ".join([*labels, "latest candle · not signals"])
            if labels
            else "No indicators selected"
        )

    def _volume_changed(self, enabled: bool) -> None:
        self._canvas.show_volume = enabled
        self._canvas.update()

    def _tool_changed(self, text: str) -> None:
        self._canvas.tool = text
        self._canvas._pending_draw = None
        self._update_drawing_buttons()

    def _latest(self) -> None:
        self._canvas.latest()

    def _undo_drawing(self) -> None:
        if self._canvas.drawings:
            self._canvas.drawings.pop()
        self._canvas._pending_draw = None
        self._update_drawing_buttons()
        self._canvas.update()

    def _clear_drawings(self) -> None:
        self._canvas.drawings.clear()
        self._canvas._pending_draw = None
        self._update_drawing_buttons()
        self._canvas.update()

    def _update_drawing_buttons(self) -> None:
        available = bool(self._canvas.drawings) or self._canvas._pending_draw is not None
        self._undo.setEnabled(available)
        self._clear.setEnabled(available)

    def _reload(self) -> None:
        if self._timeframe.currentData() == "observed":
            self._runtime.live_market.refresh_now()
            self._poll()
            return
        self._runtime.chart_data.refresh()
        self._poll(force=True)

    def _poll(self, *, force: bool = False) -> None:
        if self._runtime.is_closed:
            self._timer.stop()
            if self._expanded:
                self._expanded.close()
            return
        if self._timeframe.currentData() == "observed":
            feed = self._runtime.live_market
            self._refresh.setEnabled(not feed.busy)
            self._status.setText(
                f"Observed REST quotes only · {feed.status} · {len(self._observed)} samples · "
                "elapsed-time axis · no reconstructed OHLC"
            )
            return
        session = self._runtime.chart_data
        enabled = self._runtime.live_market.enabled and (
            self.isVisible() or self._expanded is not None
        )
        session.tick(enabled=enabled, auto_refresh=self._auto.isChecked() or force)
        self._refresh.setEnabled(not session.busy)
        if session.revision != self._revision:
            self._revision = session.revision
            self._canvas.set_series(self._instrument, session.series)
            if session.series and session.series.candles:
                index = len(session.series.candles) - 1
                hover = self._canvas._hover
                if hover and self._canvas._price_rect.contains(hover):
                    index = self._canvas._nearest(self._canvas._data_at(hover)[0])
                self._readout.setText(self._canvas.inspection(index))
            self._update_legend()
        if session.error:
            self._status.setText(
                session.error + " · last successful history retained, not refreshed"
            )
            self._canvas._empty = session.error + " · observed quotes remain a separate view"
            self._canvas.update()
        elif session.series:
            data = session.series
            tail = (
                " · latest candle may revise"
                if data.candles and data.is_forming(data.candles[-1])
                else ""
            )
            self._status.setText(
                f"{data.source} · {len(data.candles)} bars · "
                f"fetched {display_time(data.fetched_at)}"
                f"{tail} · trading-bar axis (closed-session gaps compressed)"
                + (" · polling paused" if not enabled else "")
            )
            if not data.candles:
                self._canvas._empty = "Kite returned no candles for this instrument and range"
        else:
            self._status.setText(
                "Loading Kite historical candles…"
                if session.busy
                else "Connect Kite to load history"
            )

    def _expand_chart(self) -> None:
        if self._expanded:
            self._expanded.close()
            return
        original_parent = self.parentWidget()
        original_layout = original_parent.layout() if original_parent else None
        original_index = original_layout.indexOf(self) if original_layout else -1
        original_size = self.size()
        dialog = QDialog(original_parent.window() if original_parent else None)
        dialog.setWindowTitle(f"NAYAK chart · {self._instrument} · observe-only")
        dialog.resize(1240, 760)
        layout = QVBoxLayout(dialog)
        if original_layout:
            original_layout.removeWidget(self)
        layout.addWidget(self)
        self._expand.setText("Restore")

        def restore(_result: int) -> None:
            layout.removeWidget(self)
            self.setParent(original_parent)
            if isinstance(original_layout, QVBoxLayout):
                original_layout.insertWidget(original_index, self, 1)
            elif original_layout:
                original_layout.addWidget(self)
            self.resize(original_size)
            self.show()
            self._expand.setText("Expand")
            self._expanded = None
            dialog.deleteLater()

        dialog.finished.connect(restore)
        self._expanded = dialog
        dialog.show()

    def _export_png(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save chart PNG", "nayak-chart.png", "PNG (*.png)"
        )
        if path:
            target = self._expanded or self
            self._status.setText(
                "Chart PNG saved" if target.grab().save(path, "PNG") else "Chart PNG export failed"
            )

    def _export_csv(self) -> None:
        series = self._runtime.chart_data.series
        observed = self._timeframe.currentData() == "observed"
        if not observed and (series is None or series.request.instrument != self._instrument):
            self._status.setText("No provider candles to export for this selection")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save loaded chart data", "nayak-chart.csv", "CSV (*.csv)"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                if observed:
                    writer.writerow(
                        ["source", "instrument", "provider_time_utc", "observed_ltp", "segment"]
                    )
                    writer.writerows(
                        [
                            "kite-rest-quote-v3",
                            self._instrument,
                            p.time.isoformat(),
                            p.price,
                            p.segment,
                        ]
                        for p in self._observed
                    )
                elif series is not None:
                    writer.writerow(
                        [
                            "source",
                            "instrument",
                            "interval",
                            "fetched_at_utc",
                            "bar_time_utc",
                            "open",
                            "high",
                            "low",
                            "close",
                            "volume",
                            "forming_at_capture",
                        ]
                    )
                    writer.writerows(
                        [
                            series.source,
                            self._instrument,
                            series.request.interval,
                            series.fetched_at.isoformat(),
                            b.time.isoformat(),
                            b.open,
                            b.high,
                            b.low,
                            b.close,
                            b.volume,
                            series.is_forming(b),
                        ]
                        for b in series.candles
                    )
            self._status.setText("Displayed source data exported · CSV timestamps are UTC")
        except OSError:
            self._status.setText("Chart CSV export failed; check the chosen path")
