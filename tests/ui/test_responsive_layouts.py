"""Responsive desktop contracts for common workstation components."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QLabel

from quantlab.ui.responsive import ViewportClass, responsive_state
from quantlab.ui.widgets.charts import DashboardStrip
from quantlab.ui.widgets.terminal import TerminalGrid, TerminalPanel


@pytest.fixture
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_kpi_cards_wrap_in_compact_desktop(qapp: QApplication) -> None:
    strip = DashboardStrip(["One", "Two", "Three", "Four"])
    strip.resize(900, 300)
    strip.show()
    qapp.processEvents()

    strip.apply_responsive_state(responsive_state(900, 640))
    assert strip._columns == 2
    assert strip.layout().rowCount() == 2  # type: ignore[union-attr]


def test_terminal_grid_reflows_without_recreating_panel_content(qapp: QApplication) -> None:
    panels = [TerminalPanel(str(index), QLabel(str(index))) for index in range(3)]
    grid = TerminalGrid(columns=2)
    grid.set_panels(panels)
    grid.apply_responsive_state(responsive_state(900, 640))

    assert grid._active_columns == 1
    assert grid._outer.count() == 3
    assert all(panel.parent() is not None for panel in panels)


def test_viewport_policy_prioritizes_readability() -> None:
    compact = responsive_state(900, 640)
    wide = responsive_state(1600, 900)

    assert compact.viewport is ViewportClass.COMPACT_DESKTOP
    assert compact.sidebar_icon_rail is True
    assert compact.terminal_columns == 1
    assert wide.viewport is ViewportClass.WIDE_DESKTOP
    assert wide.kpi_columns == 4
