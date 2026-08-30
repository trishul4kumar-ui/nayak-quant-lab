"""Command palette and navigation P2 tests."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from quantlab.app.bootstrap import bootstrap
from quantlab.app.settings_store import ExperienceMode
from quantlab.ui.command_registry import (
    PaletteCommand,
    build_palette_commands,
    filter_palette_commands,
)
from quantlab.ui.main_window import MainWindow
from quantlab.ui.navigation import (
    NAV_FILTER_SHORTCUT,
    NAV_SHORTCUTS,
    breadcrumb_parts,
    nav_section_header_for_page,
    shortcut_label,
)


@pytest.fixture
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_home_and_market_shortcuts_avoid_macos_conflicts() -> None:
    assert NAV_SHORTCUTS["home"] == "Meta+Shift+H"
    assert NAV_SHORTCUTS["market"] == "Meta+Shift+M"
    assert shortcut_label("home") == "⌘⇧H"
    assert shortcut_label("market") == "⌘⇧M"


def test_nav_filter_shortcut_defined() -> None:
    assert NAV_FILTER_SHORTCUT == "Meta+U"


def test_breadcrumb_parts_and_section_lookup() -> None:
    section, page = breadcrumb_parts("backtests")
    assert section == "Validate"
    assert page == "Backtests"
    assert nav_section_header_for_page("backtests") == "__h_validate"


def test_palette_fuzzy_ranking_prefers_title_prefix() -> None:
    commands = [
        PaletteCommand("nav:compare", "nav", "Compare", "Go", ("compare",)),
        PaletteCommand("nav:validation", "nav", "Validation", "Go", ("validation",)),
    ]
    ranked = filter_palette_commands(commands, "comp")
    assert ranked[0].command_id == "nav:compare"


def test_palette_recents_surface_first_when_empty_query() -> None:
    commands = [
        PaletteCommand("nav:home", "nav", "Home", "Go", ("home",)),
        PaletteCommand("nav:compare", "nav", "Compare", "Go", ("compare",)),
    ]
    ranked = filter_palette_commands(commands, "", recents=["nav:compare"])
    assert ranked[0].command_id == "nav:compare"


@pytest.mark.desktop
def test_main_window_nav_filter_shortcut_focuses_search(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    runtime.ui_settings.current.experience_mode = ExperienceMode.FULL
    window = MainWindow(runtime)
    window.show()
    qapp.processEvents()
    window._focus_nav_search()
    qapp.processEvents()
    assert window._nav_search.hasFocus()
    window.close()


@pytest.mark.desktop
def test_palette_recents_persist(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    window = MainWindow(runtime)
    window._record_palette_command("nav:compare")
    window._record_palette_command("nav:validation")
    recents = runtime.ui_settings.current.palette_recents
    assert recents[0] == "nav:validation"
    assert "nav:compare" in recents
    window.close()


@pytest.mark.desktop
def test_build_palette_includes_experiments(tmp_path: Path) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    commands = build_palette_commands(runtime)
    kinds = {cmd.kind for cmd in commands}
    assert "nav" in kinds
    assert "action" in kinds
