"""Pulse dashboard tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.app.bootstrap import bootstrap
from quantlab.app.pulse import build_pulse_items, status_tone


def test_status_tone_ready_is_ok() -> None:
    assert status_tone("DATA", "READY") == "ok"
    assert status_tone("RISK", "ARMED") == "warn"


def test_build_pulse_items_has_eight_cards(tmp_path: Path) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    summary, items, tone = build_pulse_items(runtime)
    assert len(items) == 8
    assert items[0].title == "System"
    assert "research" in summary.lower() or tone in {"ok", "warn", "bad"}
    keys = {item.nav_key for item in items if item.nav_key}
    assert "system" in keys
    assert "data" in keys
    assert "broker" in keys


@pytest.mark.desktop
def test_pulse_panel_renders(tmp_path: Path) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from quantlab.ui.widgets.pulse_panel import PulsePanel

    app = QApplication.instance() or QApplication([])
    runtime = bootstrap(data_dir=tmp_path)
    panel = PulsePanel()
    panel.refresh(runtime)
    panel.show()
    app.processEvents()
