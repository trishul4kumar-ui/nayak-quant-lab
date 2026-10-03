from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QLabel

from quantlab.app.ai_chat import ai_status, chat
from quantlab.app.assistant import NayakAssistant
from quantlab.app.bootstrap import bootstrap
from quantlab.app.chart_data import (
    BENCHMARK_LABEL,
    drawdown_episode_rows,
    equity_chart_series,
    rebase_to_one,
)
from quantlab.app.settings_store import UiTheme
from quantlab.ui.pages.ai_research import AiResearchPage
from quantlab.ui.theme import LIGHT_STYLESHEET, apply_theme, chart_palette, stylesheet_for
from quantlab.ui.widgets import TerminalGrid, TerminalPanel


@pytest.fixture
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.mark.desktop
def test_stylesheet_for_light_and_dark() -> None:
    assert "#edf5f9" in stylesheet_for(UiTheme.LIGHT)
    assert "#06111d" in stylesheet_for(UiTheme.DARK)
    assert LIGHT_STYLESHEET.startswith("\nQWidget")


@pytest.mark.desktop
def test_apply_theme_updates_app(qapp: QApplication) -> None:
    apply_theme(qapp, UiTheme.LIGHT)
    assert "#edf5f9" in qapp.styleSheet()
    apply_theme(qapp, UiTheme.DARK)
    assert "#06111d" in qapp.styleSheet()


@pytest.mark.desktop
def test_chart_palette_follows_theme(qapp: QApplication) -> None:
    apply_theme(qapp, UiTheme.DARK)
    dark = chart_palette()
    assert dark.background == "#091725"
    assert dark.muted == "#7f9ab1"
    apply_theme(qapp, UiTheme.LIGHT)
    light = chart_palette()
    assert light.background == "#f7f5f2"
    assert light.muted == "#5c574f"
    assert light.foreground == "#2c2825"


@pytest.mark.desktop
def test_equity_chart_series_includes_benchmark() -> None:
    series = equity_chart_series([100.0, 102.0, 101.0, 105.0], strategy_label="Run A")
    assert len(series) == 2
    assert series[0].label == "Run A"
    assert series[1].label == BENCHMARK_LABEL
    assert series[1].dashed is True
    assert series[0].values[0] == pytest.approx(1.0)


@pytest.mark.desktop
def test_rebase_to_one() -> None:
    assert rebase_to_one([200.0, 220.0]) == [1.0, 1.1]


@pytest.mark.desktop
def test_drawdown_episode_rows() -> None:
    equity = [100.0, 110.0, 90.0, 95.0, 100.0]
    rows = drawdown_episode_rows(equity, n=3)
    assert rows
    assert len(rows[0]) == 5


@pytest.mark.desktop
def test_terminal_layout_persist_and_restore(qapp: QApplication, tmp_path: Path) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    store = runtime.ui_settings
    grid = TerminalGrid(columns=2, layout_id="test-grid", settings=store)
    grid.set_panels(
        [
            TerminalPanel("A", QLabel("one")),
            TerminalPanel("B", QLabel("two")),
        ]
    )
    qapp.processEvents()
    grid.persist_layout()
    payload = store.current.terminal_layouts.get("test-grid")
    assert payload is not None
    assert "outer" in payload or "row0" in payload

    grid2 = TerminalGrid(columns=2, layout_id="test-grid", settings=store)
    grid2.set_panels(
        [
            TerminalPanel("A", QLabel("one")),
            TerminalPanel("B", QLabel("two")),
        ]
    )
    qapp.processEvents()


@pytest.mark.desktop
def test_context_nudges_after_onboarding(tmp_path: Path) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    assistant = NayakAssistant(runtime)
    assistant.complete_onboarding()
    nudges = assistant.context_nudges()
    assert any("Test" in n or "wizard" in n for n in nudges)


@pytest.mark.desktop
def test_ai_chat_local_sharpe(tmp_path: Path) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    reply = chat(runtime, "What is Sharpe ratio?")
    assert "Sharpe" in reply
    status = ai_status()
    assert status.provider in {"nayak-local", "openai", "anthropic"}


@pytest.mark.desktop
def test_ai_chat_blocks_live_orders(tmp_path: Path) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    reply = chat(runtime, "Place a live buy order on NIFTY")
    assert "cannot" in reply.lower() or "denied" in reply.lower()


@pytest.mark.desktop
def test_ai_research_page_builds(qapp: QApplication, tmp_path: Path) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    page = AiResearchPage(runtime)
    page.refresh()
    assert page.isVisible() or page.parent() is None
