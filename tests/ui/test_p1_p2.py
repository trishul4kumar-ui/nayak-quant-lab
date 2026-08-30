from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.app.bootstrap import bootstrap
from quantlab.app.settings_store import ExperienceMode
from quantlab.ui.navigation import FULL_NAV, nav_for_mode


@pytest.mark.desktop
def test_full_nav_pipeline_sections() -> None:
    labels = [item.label for item in FULL_NAV if item.header]
    assert "— Research —" in labels
    assert "— Validate —" in labels
    assert "— Execute —" in labels
    assert "— Recent —" not in labels


@pytest.mark.desktop
def test_full_nav_no_recent_section() -> None:
    items = nav_for_mode(ExperienceMode.FULL)
    labels = [item.label for item in items if item.header]
    assert "— Recent —" not in labels


@pytest.mark.desktop
def test_sidebar_collapsed_persisted(tmp_path: Path) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    runtime.ui_settings.current.sidebar_collapsed = True
    runtime.ui_settings.save()
    loaded = bootstrap(data_dir=tmp_path)
    assert loaded.ui_settings.current.sidebar_collapsed is True
