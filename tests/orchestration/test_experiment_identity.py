from __future__ import annotations

import pytest

from quantlab.orchestration.registry import get_spec


@pytest.mark.orchestration
def test_frozen_spec_hash() -> None:
    spec = get_spec("EXP-MOM-001")
    again = get_spec("EXP-MOM-001")
    assert spec.identity_hash() == again.identity_hash()
    assert spec.config_hash() == spec.identity_hash()
    changed = spec.model_copy(update={"cost_bps": 15.0})
    assert changed.identity_hash() != spec.identity_hash()
