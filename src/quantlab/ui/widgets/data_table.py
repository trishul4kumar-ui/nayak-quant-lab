"""Data tables with badges, truncation, and gate coloring."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QColor, QKeyEvent
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

from quantlab.app.settings_store import UiTheme
from quantlab.ui.theme import active_ui_theme

_EXPERIMENT_FIELD_NAMES = frozenset(
    {
        "experiment",
        "experiment_id",
        "ledger id",
        "id",
    }
)


def truncate_text(text: str, max_len: int = 16) -> str:
    cleaned = str(text)
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 1] + "…"


def fill_table(
    table: QTableWidget,
    headers: list[str],
    rows: list[list[str]],
    *,
    badge_columns: set[int] | None = None,
    truncate_columns: set[int] | None = None,
    experiment_links: dict[tuple[int, int], str] | None = None,
) -> None:
    badge_columns = badge_columns or set()
    truncate_columns = truncate_columns or set()
    experiment_links = experiment_links or {}
    table.clear()
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setRowCount(len(rows))
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    table.setAlternatingRowColors(False)
    table.setShowGrid(False)
    table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    header = table.horizontalHeader()
    header.setSectionsMovable(True)
    header.setStretchLastSection(True)
    header.setDefaultSectionSize(max(header.defaultSectionSize(), 120))

    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            text = str(cell)
            full_id = experiment_links.get((r, c))
            if full_id:
                text = truncate_text(full_id, 20)
            elif c in truncate_columns:
                text = truncate_text(text, 20)
            item = QTableWidgetItem(text)
            if full_id:
                item.setData(Qt.ItemDataRole.UserRole, full_id)
                item.setForeground(QColor("#42a5f5"))
                item.setToolTip("Double-click or press Enter to open in journal")
            if c in badge_columns:
                color = _result_color(text)
                if color is not None and not full_id:
                    item.setForeground(color)
                    item.setBackground(_result_background(text))
            table.setItem(r, c, item)
    table.resizeColumnsToContents()


def fill_field_value_table(
    table: QTableWidget,
    pairs: list[tuple[str, str]],
    *,
    value_badges: bool = True,
    journal_fields: frozenset[str] = _EXPERIMENT_FIELD_NAMES,
) -> None:
    rows = [[k, v] for k, v in pairs]
    links: dict[tuple[int, int], str] = {}
    for r, (field, value) in enumerate(pairs):
        if field.strip().lower() in journal_fields and value and value != "—":
            links[(r, 1)] = value
    fill_table(
        table,
        ["Field", "Value"],
        rows,
        badge_columns={1} if value_badges else set(),
        truncate_columns={1},
        experiment_links=links,
    )


class _JournalLinkFilter(QObject):
    def __init__(self, table: QTableWidget, on_open: Callable[[str], None]) -> None:
        super().__init__(table)
        self._table = table
        self._on_open = on_open

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj is self._table and event.type() == QEvent.Type.KeyPress:
            key_event = event
            if isinstance(key_event, QKeyEvent) and key_event.key() in (
                Qt.Key.Key_Return,
                Qt.Key.Key_Enter,
            ):
                row = self._table.currentRow()
                if row >= 0:
                    for col in range(self._table.columnCount()):
                        item = self._table.item(row, col)
                        if item is None:
                            continue
                        exp_id = item.data(Qt.ItemDataRole.UserRole)
                        if exp_id:
                            self._on_open(str(exp_id))
                            return True
        return super().eventFilter(obj, event)


def wire_journal_links(
    table: QTableWidget,
    on_open: Callable[[str], None],
) -> None:
    if getattr(table, "_journal_links_wired", False):
        return
    table._journal_links_wired = True  # type: ignore[attr-defined]

    def _on_click(row: int, col: int) -> None:
        item = table.item(row, col)
        if item is None:
            return
        exp_id = item.data(Qt.ItemDataRole.UserRole)
        if exp_id:
            on_open(str(exp_id))

    table.cellDoubleClicked.connect(_on_click)
    filt = _JournalLinkFilter(table, on_open)
    table.installEventFilter(filt)
    table._journal_link_filter = filt  # type: ignore[attr-defined]


def _result_color(value: str) -> QColor | None:
    lowered = value.strip().lower()
    if lowered in {"pass", "passed", "ok", "true", "ready", "healthy"}:
        return QColor("#26a69a")
    if lowered in {"warn", "warning"}:
        return QColor("#ffb74d")
    if lowered in {"fail", "failed", "false", "blocked", "disabled", "disconnected"}:
        return QColor("#ef5350")
    if lowered == "synthetic":
        return QColor("#c9a96e")
    return None


def _result_background(value: str) -> QColor:
    lowered = value.strip().lower()
    light = active_ui_theme() is UiTheme.LIGHT
    if light:
        if lowered in {"pass", "passed", "ok", "true", "ready", "healthy"}:
            return QColor("#d4ede8")
        if lowered in {"warn", "warning"}:
            return QColor("#fff3e0")
        if lowered in {"fail", "failed", "false", "blocked", "disabled", "disconnected"}:
            return QColor("#fde8e8")
        return QColor("#f7f5f2")
    if lowered in {"pass", "passed", "ok", "true", "ready", "healthy"}:
        return QColor("#1a2e28")
    if lowered in {"warn", "warning"}:
        return QColor("#2e2a1a")
    if lowered in {"fail", "failed", "false", "blocked", "disabled", "disconnected"}:
        return QColor("#2e1a1a")
    return QColor("#252932")
