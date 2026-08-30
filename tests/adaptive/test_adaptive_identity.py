"""Adaptive identity is hashed; overwrites are refused."""

from __future__ import annotations

import pytest

from quantlab.adaptive.registry import AdaptiveRegistry, get_adaptive_model


@pytest.mark.adaptive
def test_identity_changes_when_window_changes() -> None:
    base = get_adaptive_model("rolling_ic_mom20")
    changed = base.model_copy(update={"version": "2", "window": 40})
    assert changed.identity_hash() != base.identity_hash()


@pytest.mark.adaptive
def test_registry_refuses_overwrite() -> None:
    registry = AdaptiveRegistry()
    with pytest.raises(ValueError, match="cannot overwrite"):
        registry.register(get_adaptive_model("static_mom20"))
