"""Tests for the shared lab design system."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QTableWidget

from quantlab.ui.navigation import FULL_NAV, breadcrumb_for_key, filter_collapsed_sections
from quantlab.ui.time_format import format_ist_from_iso
from quantlab.ui.widgets.data_table import fill_table
from quantlab.ui.widgets.lab_shell import StatusBadge, badge_for_value


@pytest.fixture
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_status_badge_kinds(qapp: QApplication) -> None:
    assert StatusBadge("pass").text() == "PASS"
    assert badge_for_value("fail") is not None


def test_fill_table_gate_colors(qapp: QApplication) -> None:
    table = QTableWidget()
    fill_table(
        table,
        ["Check", "Result"],
        [["integrity", "pass"], ["cost", "fail"]],
        badge_columns={1},
    )
    assert table.rowCount() == 2
    assert table.item(0, 1).foreground().color().name() != ""


def test_breadcrumb_for_alpha() -> None:
    assert "Research" in breadcrumb_for_key("alpha")
    assert "Alpha" in breadcrumb_for_key("alpha")


def test_collapsed_nav_hides_items() -> None:
    items = list(FULL_NAV)
    folded = filter_collapsed_sections(items, frozenset({"__h_validate"}))
    keys = [item.key for item in folded if not item.header]
    assert "backtests" not in keys
    assert "portfolio" in keys


def test_ist_relative_timestamp() -> None:
    from datetime import UTC, datetime

    recent = datetime.now(tz=UTC).isoformat()
    assert format_ist_from_iso(recent) in {"just now", "1 min ago"}
    absolute = format_ist_from_iso(recent, relative=False)
    assert absolute.endswith("IST")
