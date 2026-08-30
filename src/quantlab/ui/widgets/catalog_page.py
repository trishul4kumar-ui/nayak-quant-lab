"""Template for seed-catalog + last-run lab pages."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QTableWidget, QVBoxLayout, QWidget

from quantlab.ui.widgets.charts import DashboardStrip, SparklineWidget
from quantlab.ui.widgets.data_table import fill_field_value_table, fill_table
from quantlab.ui.widgets.lab_shell import EmptyState, LabPageShell, data_kind_badge


class CatalogLabPage(LabPageShell):
    def __init__(
        self,
        title: str,
        *,
        subtitle: str,
        nayak_summary: str,
        technical: str = "",
        catalog_title: str = "Seed catalog",
        catalog_headers: list[str] | None = None,
        last_title: str = "Last experiment",
        empty_title: str = "No runs yet",
        empty_body: str = "Run a backtest from Test or Backtest Lab — results appear here.",
        empty_action: str | None = "Run backtest →",
        on_empty_action: Callable[[], None] | None = None,
        dashboard_titles: list[str] | None = None,
        sparkline: bool = False,
    ) -> None:
        super().__init__(
            title,
            subtitle=subtitle,
            nayak_summary=nayak_summary,
            technical=technical,
        )
        self._catalog_headers = catalog_headers or ["Item", "Detail"]
        self._on_empty_action = on_empty_action

        body = self.body()
        insert_at = 1  # after running banner
        self._dash: DashboardStrip | None = None
        if dashboard_titles:
            self._dash = DashboardStrip(dashboard_titles)
            body.insertWidget(insert_at, self._dash)
            insert_at += 1
        self._spark: SparklineWidget | None = None
        if sparkline:
            self._spark = SparklineWidget(min_height=56)
            body.insertWidget(insert_at, self._spark)
            insert_at += 1

        cat_label = QLabel(catalog_title)
        cat_label.setObjectName("sectionTitle")
        cat_label.setStyleSheet("font-weight: 600; font-size: 13px;")
        self.catalog = QTableWidget()
        body.insertWidget(insert_at, cat_label)
        body.insertWidget(insert_at + 1, self.catalog, 2)

        self._last_label: QLabel | None = None
        if last_title:
            last_label = QLabel(last_title)
            last_label.setObjectName("sectionTitle")
            last_label.setStyleSheet("font-weight: 600; font-size: 13px;")
            self._last_label = last_label
            self._last_frame = QFrame()
            self._last_frame.setObjectName("card")
            last_layout = QVBoxLayout(self._last_frame)
            last_layout.setContentsMargins(12, 12, 12, 12)
            self._data_kind_row = QHBoxLayout()
            self._data_kind_row.addStretch()
            last_layout.addLayout(self._data_kind_row)
            self.last = QTableWidget()
            last_layout.addWidget(self.last)
            self._empty = EmptyState(
                empty_title,
                empty_body,
                action_label=empty_action,
                on_action=on_empty_action,
            )
            self._empty.setVisible(False)
            last_layout.addWidget(self._empty)
            body.addWidget(last_label)
            body.addWidget(self._last_frame, 1)
        else:
            self._last_frame = QFrame()
            self.last = QTableWidget()
            self._empty = EmptyState(empty_title, empty_body)

    @property
    def dashboard(self) -> DashboardStrip | None:
        return self._dash

    @property
    def sparkline(self) -> SparklineWidget | None:
        return self._spark

    def set_catalog_rows(self, rows: list[list[str]]) -> None:
        fill_table(
            self.catalog,
            self._catalog_headers,
            rows,
            truncate_columns={len(self._catalog_headers) - 1},
        )

    def set_last_run(self, pairs: list[tuple[str, str]] | None) -> None:
        if not self._last_label:
            return
        self._clear_data_kind_badge()
        if not pairs:
            self.last.setVisible(False)
            self._empty.setVisible(True)
            return
        self.last.setVisible(True)
        self._empty.setVisible(False)
        for field, value in pairs:
            if field.strip().lower() in {"data", "data_kind"} and value and value != "—":
                self._data_kind_row.insertWidget(0, data_kind_badge(value))
                break
        fill_field_value_table(self.last, pairs)

    def _clear_data_kind_badge(self) -> None:
        if not hasattr(self, "_data_kind_row"):
            return
        while self._data_kind_row.count():
            item = self._data_kind_row.takeAt(0)
            if item is None:
                break
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._data_kind_row.addStretch()

    def set_empty_action(
        self,
        on_action: Callable[[], None] | None,
        *,
        action_label: str | None = "Run backtest →",
    ) -> None:
        self._on_empty_action = on_action
        self._empty.set_action(action_label, on_action)

    def insert_before_last_run(self, widget: QWidget, *, label: QLabel | None = None) -> None:
        """Insert a widget (and optional section label) before the last-run block."""
        body = self.body()
        insert_at = body.count() - 2 if self._last_label is not None else body.count()
        if label is not None:
            body.insertWidget(insert_at, label)
            insert_at += 1
        body.insertWidget(insert_at, widget)
