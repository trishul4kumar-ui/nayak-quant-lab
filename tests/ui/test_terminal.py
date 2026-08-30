from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QLabel

from quantlab.ui.widgets import EXPLANATIONS, TerminalGrid, TerminalPanel, WatchlistWidget


@pytest.fixture
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.mark.desktop
def test_explain_copy_has_core_metrics() -> None:
    for key in ("sharpe", "momentum_20", "look_ahead_bias", "equity_curve"):
        assert key in EXPLANATIONS
        assert len(EXPLANATIONS[key]) > 20


@pytest.mark.desktop
def test_terminal_grid_hosts_panels(qapp: QApplication) -> None:
    grid = TerminalGrid(columns=2)
    panels = [
        TerminalPanel("A", QLabel("one")),
        TerminalPanel("B", QLabel("two")),
    ]
    grid.set_panels(panels)
    assert len(panels) == 2


@pytest.mark.desktop
def test_watchlist_emits_selection(qapp: QApplication) -> None:
    watch = WatchlistWidget()
    seen: list[str] = []
    watch.instrument_selected.connect(lambda row: seen.append(str(row["instrument"])))
    watch.set_market_rows(
        [
            {
                "instrument": "SYN01",
                "name": "Syn One",
                "close": 100.0,
                "volume": 1000.0,
                "momentum_20": 0.05,
                "as_of": "2026-01-01",
            }
        ]
    )
    qapp.processEvents()
    assert seen == ["SYN01"]
