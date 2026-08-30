"""P6 — Quality pass: tests, theme, accessibility, performance."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication, QTableWidget

from quantlab.app.bootstrap import bootstrap
from quantlab.app.mode import AppMode
from quantlab.app.settings_store import ExperienceMode, UiTheme
from quantlab.ui.main_window import MainWindow
from quantlab.ui.theme import LIGHT_STYLESHEET, active_ui_theme, apply_theme, stylesheet_for
from quantlab.ui.widgets.data_table import fill_table, wire_journal_links
from quantlab.ui.widgets.footer_status import FooterStatusBar


@pytest.fixture
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.mark.desktop
def test_footer_broker_chip_navigates(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    runtime.ui_settings.current.experience_mode = ExperienceMode.FULL
    window = MainWindow(runtime)
    window.show()
    qapp.processEvents()
    window.status_bar.chip_clicked.emit("broker")
    qapp.processEvents()
    assert runtime.ui_settings.current.nav == "broker"
    window.close()


@pytest.mark.desktop
def test_nav_live_tint_when_live_mode(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    window = MainWindow(runtime)
    runtime.mode = AppMode.LIVE
    window._apply_live_chrome()
    assert window._nav_host.objectName() == "navHostLive"
    assert not window._live_banner.isHidden()
    assert window._mode_badge.objectName() == "modeBadgeLive"
    runtime.mode = AppMode.RESEARCH
    window.close()


@pytest.mark.desktop
def test_collapsed_icon_rail_tooltips(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    runtime.ui_settings.current.experience_mode = ExperienceMode.FULL
    runtime.ui_settings.current.sidebar_collapsed = True
    window = MainWindow(runtime)
    window.show()
    qapp.processEvents()
    tips = [
        window.nav.item(i).toolTip()
        for i in range(window.nav.count())
        if window.nav.item(i) and window._row_to_key[i]
    ]
    assert tips
    assert any(" · " in tip for tip in tips)
    window.close()


@pytest.mark.desktop
def test_tick_uses_pulse_only_not_full_home_refresh(
    tmp_path: Path, qapp: QApplication, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    runtime.ui_settings.current.nav = "home"
    window = MainWindow(runtime)
    full_refresh = MagicMock()
    pulse_refresh = MagicMock()
    monkeypatch.setattr(window.home, "refresh", full_refresh)
    monkeypatch.setattr(window.home, "refresh_pulse", pulse_refresh)
    window._last_status_sig = window._status_signature()
    window._tick()
    pulse_refresh.assert_called_once()
    full_refresh.assert_not_called()
    window.close()


@pytest.mark.desktop
def test_tick_skips_footer_rebuild_when_unchanged(
    tmp_path: Path, qapp: QApplication, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    window = MainWindow(runtime)
    paint = MagicMock()
    monkeypatch.setattr(window, "_paint_status", paint)
    window._last_status_sig = window._status_signature()
    window._tick()
    paint.assert_not_called()
    window.close()


def test_light_theme_has_focus_rings() -> None:
    assert "QPushButton:focus" in LIGHT_STYLESHEET
    assert "QTableWidget:focus" in LIGHT_STYLESHEET
    assert "#3d7a8c" in LIGHT_STYLESHEET


def test_stylesheet_for_light_includes_nav_live_tint() -> None:
    sheet = stylesheet_for(UiTheme.LIGHT)
    assert "navHostLive" in sheet
    assert "#f5e8e8" in sheet


def test_apply_theme_tracks_active_theme(qapp: QApplication) -> None:
    apply_theme(qapp, UiTheme.LIGHT)
    assert active_ui_theme() is UiTheme.LIGHT
    apply_theme(qapp, UiTheme.DARK)
    assert active_ui_theme() is UiTheme.DARK


@pytest.mark.desktop
def test_journal_table_enter_opens_link(qapp: QApplication) -> None:
    table = QTableWidget()
    opened: list[str] = []
    fill_table(
        table,
        ["Field", "Value"],
        [["experiment", "abc123def456"]],
        experiment_links={(0, 1): "abc123def456"},
    )
    wire_journal_links(table, opened.append)
    table.setCurrentCell(0, 1)
    event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
    qapp.sendEvent(table, event)
    assert opened == ["abc123def456"]


@pytest.mark.desktop
def test_footer_status_light_theme_contrast(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    runtime.ui_settings.current.theme = UiTheme.LIGHT
    bar = FooterStatusBar()
    bar.update_from_runtime(runtime, mode_label="FULL LAB")
    qapp.processEvents()
    chip = bar._layout.itemAt(0).widget()
    assert chip is not None
    assert "#d4ede8" in chip.styleSheet() or "#f0ebe3" in chip.styleSheet()


@pytest.mark.desktop
def test_settings_clear_palette_recents(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    runtime.ui_settings.current.palette_recents = ["nav:compare", "nav:validation"]
    runtime.ui_settings.save()
    window = MainWindow(runtime)
    window.settings._clear_palette_recents()
    assert runtime.ui_settings.current.palette_recents == []
    window.close()
