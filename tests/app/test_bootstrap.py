import sys
from pathlib import Path

import pytest

from quantlab.app.bootstrap import bootstrap
from quantlab.app.mode import AppMode
from quantlab.core.errors import SafetyError


def test_bootstrap_does_not_import_qt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QUANT_LAB_DATA_DIR", str(tmp_path))
    before = {name for name in sys.modules if name.startswith("PySide6")}
    runtime = bootstrap(data_dir=tmp_path)
    after = {name for name in sys.modules if name.startswith("PySide6")}
    assert after == before
    assert runtime.mode is AppMode.RESEARCH
    assert runtime.gates.live_trading is False
    assert runtime.health.research_ready()
    runtime.shutdown()


def test_bootstrap_live_env_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QUANT_LAB_MODE", "live")
    runtime = bootstrap(data_dir=tmp_path)
    assert runtime.mode is AppMode.RESEARCH
    runtime.shutdown()


def test_try_enable_live_blocked(tmp_path: Path) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    with pytest.raises(SafetyError):
        runtime.try_enable_live()
    runtime.shutdown()


def test_ui_settings_persist(tmp_path: Path) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    runtime.ui_settings.current.width = 1111
    runtime.shutdown()
    again = bootstrap(data_dir=tmp_path)
    assert again.ui_settings.current.width == 1111
    again.shutdown()
