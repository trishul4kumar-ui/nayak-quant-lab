from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.app.assistant import FocusAction, NayakAssistant
from quantlab.app.bootstrap import bootstrap
from quantlab.app.settings_store import ExperienceMode


@pytest.mark.desktop
def test_nayak_greeting_uses_tk_name(tmp_path: Path) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    runtime.ui_settings.current.tk_display_name = "TK"
    assistant = NayakAssistant(runtime)
    greeting = assistant.greeting()
    assert "TK" in greeting
    assert greeting.startswith(("Good morning", "Good afternoon", "Good evening"))


@pytest.mark.desktop
def test_focus_onboarding_before_milestone(tmp_path: Path) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    assistant = NayakAssistant(runtime)
    focus = assistant.focus()
    assert focus.action is FocusAction.ONBOARDING
    assistant.complete_onboarding()
    focus2 = assistant.focus()
    assert focus2.action is FocusAction.FIRST_BACKTEST


@pytest.mark.desktop
def test_ui_settings_default_guided_home(tmp_path: Path) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    prefs = runtime.ui_settings.current
    assert prefs.experience_mode is ExperienceMode.GUIDED
    assert prefs.nav == "home"
    assert prefs.tk_display_name == "TK"
