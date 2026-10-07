from __future__ import annotations

import sys
from importlib import import_module

import pytest

from quantlab.cli import main


@pytest.mark.parametrize("enabled", [False, True])
def test_desktop_kite_startup_option_is_explicit(
    enabled: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[bool] = []
    monkeypatch.setattr(
        import_module("quantlab.ui.main"),
        "main",
        lambda *, kite_quotes=False: requests.append(kite_quotes) or 0,
    )
    monkeypatch.setattr(
        sys, "argv", ["quantlab", "desktop", *(["--kite-quotes"] if enabled else [])]
    )
    with pytest.raises(SystemExit) as result:
        main()
    assert result.value.code == 0 and requests == [enabled]
