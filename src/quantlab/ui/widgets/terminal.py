from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from quantlab.app.settings_store import UiSettingsStore
from quantlab.ui.widgets.explain import ExplainChip


class TerminalPanel(QFrame):
    """Mosaic panel — terminal chrome with optional explain chip and expand."""

    expand_requested = Signal()

    def __init__(
        self,
        title: str,
        content: QWidget,
        *,
        explain_key: str | None = None,
    ) -> None:
        super().__init__()
        self.setObjectName("terminalPanel")
        self.setAccessibleName(f"{title} terminal panel")
        self._content = content
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        header = QHBoxLayout()
        title_label = QLabel(title.upper())
        title_label.setObjectName("terminalPanelTitle")
        title_label.setStyleSheet("font-size: 11px; font-weight: 700; letter-spacing: 1px;")
        header.addWidget(title_label)
        if explain_key:
            chip = ExplainChip(explain_key)
            header.addWidget(chip)
        header.addStretch()
        self._focus = QPushButton("Focus")
        self._focus.setObjectName("panelFocus")
        self._focus.setCheckable(True)
        self._focus.setToolTip("Focus this panel; click again to restore the layout")
        self._focus.clicked.connect(self.expand_requested.emit)
        header.addWidget(self._focus)
        root.addLayout(header)
        root.addWidget(content, 1)

    def set_focused(self, focused: bool) -> None:
        self._focus.blockSignals(True)
        self._focus.setChecked(focused)
        self._focus.setText("Restore" if focused else "Focus")
        self._focus.blockSignals(False)


class TerminalGrid(QWidget):
    """Resizable split workspace with optional persisted splitter sizes."""

    def __init__(
        self,
        *,
        columns: int = 2,
        layout_id: str | None = None,
        settings: UiSettingsStore | None = None,
    ) -> None:
        super().__init__()
        self._columns = max(1, columns)
        self._layout_id = layout_id
        self._settings = settings
        self._outer = QSplitter(Qt.Orientation.Vertical)
        self._outer.setChildrenCollapsible(False)
        self._outer.setHandleWidth(8)
        self._outer.setOpaqueResize(True)
        self._row_splitters: list[QSplitter] = []
        self._panels: list[TerminalPanel] = []
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(self._outer)
        self._outer.splitterMoved.connect(self._on_splitter_moved)
        self._focused_panel: TerminalPanel | None = None

    def set_panels(self, panels: list[TerminalPanel]) -> None:
        self._panels = panels
        while self._outer.count():
            widget = self._outer.widget(0)
            if widget is not None:
                widget.setParent(None)
        self._row_splitters.clear()

        if not panels:
            return

        cols = self._columns
        rows: list[list[TerminalPanel]] = []
        for i in range(0, len(panels), cols):
            rows.append(panels[i : i + cols])

        for row_panels in rows:
            row_splitter = QSplitter(Qt.Orientation.Horizontal)
            row_splitter.setChildrenCollapsible(False)
            row_splitter.setHandleWidth(8)
            row_splitter.setOpaqueResize(True)
            for panel in row_panels:
                panel.expand_requested.connect(self._make_expand_handler(panel))
                row_splitter.addWidget(panel)
                row_splitter.splitterMoved.connect(self._on_splitter_moved)
            row_splitter.setStretchFactor(0, 2 if len(row_panels) > 1 else 1)
            if len(row_panels) > 1:
                row_splitter.setStretchFactor(1, 1)
            self._row_splitters.append(row_splitter)
            self._outer.addWidget(row_splitter)

        for splitter in [self._outer, *self._row_splitters]:
            for index in range(1, splitter.count()):
                splitter.handle(index).setToolTip("Drag to resize terminal panels")

        if len(rows) == 1:
            self._outer.setStretchFactor(0, 1)
        else:
            self._outer.setStretchFactor(0, 2)
            self._outer.setStretchFactor(1, 1)
        self._restore_layout()

    def persist_layout(self) -> None:
        if self._layout_id is None or self._settings is None:
            return
        payload = self._snapshot_layout()
        if not payload:
            return
        self._settings.current.terminal_layouts[self._layout_id] = payload
        self._settings.save()

    def _on_splitter_moved(self, *_args: object) -> None:
        self.persist_layout()

    def _snapshot_layout(self) -> dict[str, list[int]]:
        payload: dict[str, list[int]] = {}
        outer_sizes = self._outer.sizes()
        if outer_sizes:
            payload["outer"] = outer_sizes
        for index, splitter in enumerate(self._row_splitters):
            sizes = splitter.sizes()
            if sizes:
                payload[f"row{index}"] = sizes
        return payload

    def _restore_layout(self) -> None:
        if self._layout_id is None or self._settings is None:
            return
        payload = self._settings.current.terminal_layouts.get(self._layout_id)
        if not payload:
            return
        outer = payload.get("outer")
        if outer and len(outer) == self._outer.count():
            self._outer.setSizes(outer)
        for index, splitter in enumerate(self._row_splitters):
            sizes = payload.get(f"row{index}")
            if sizes and len(sizes) == splitter.count():
                splitter.setSizes(sizes)

    def _make_expand_handler(self, panel: TerminalPanel) -> Callable[[], None]:
        def _expand() -> None:
            if self._focused_panel is panel:
                self.reset_layout()
                return
            if self._focused_panel is not None:
                self._focused_panel.set_focused(False)
            self._focused_panel = panel
            panel.set_focused(True)
            for row_splitter in self._row_splitters:
                sizes = []
                for i in range(row_splitter.count()):
                    widget = row_splitter.widget(i)
                    sizes.append(1000 if widget is panel else 1)
                if sizes:
                    row_splitter.setSizes(sizes)
            self.persist_layout()

        return _expand

    def reset_layout(self) -> None:
        if self._focused_panel is not None:
            self._focused_panel.set_focused(False)
            self._focused_panel = None
        self._outer.setSizes([100] * self._outer.count())
        for splitter in self._row_splitters:
            splitter.setSizes([100] * splitter.count())
        self.persist_layout()


class WatchlistWidget(QTableWidget):
    """Color-coded instrument table — click a row for detail."""

    instrument_selected = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        mono = QFont("Menlo", 13)
        mono.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(mono)
        self._rows: list[dict[str, Any]] = []
        self.cellClicked.connect(self._on_cell)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

    def set_market_rows(self, rows: list[dict[str, Any]]) -> None:
        self._rows = list(rows)
        headers = ["Instrument", "Close ₹", "Volume", "Mom 20", "As of"]
        self.clear()
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.setRowCount(len(rows))
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        header = self.horizontalHeader()
        header.setSectionsMovable(True)
        header.setStretchLastSection(True)

        for r, row in enumerate(rows):
            mom = row.get("momentum_20")
            cells = [
                str(row["instrument"]),
                f"{row['close']:.2f}",
                f"{row['volume']:.0f}",
                "" if mom is None else f"{mom:.4f}",
                str(row["as_of"]),
            ]
            tint = QColor("#1e222d")
            if isinstance(mom, float):
                tint = QColor("#1a2e28") if mom >= 0 else QColor("#2e1a1a")
            for c, cell in enumerate(cells):
                item = QTableWidgetItem(cell)
                item.setBackground(tint)
                if c == 1 and isinstance(mom, float):
                    item.setForeground(QColor("#26a69a") if mom >= 0 else QColor("#ef5350"))
                self.setItem(r, c, item)
        self.resizeColumnsToContents()
        if rows:
            self.selectRow(0)
            self.instrument_selected.emit(rows[0])

    def _on_cell(self, row: int, _col: int) -> None:
        if 0 <= row < len(self._rows):
            self.instrument_selected.emit(self._rows[row])
