"""Regime and state-variable identity is hashed; overwrites are refused."""

from __future__ import annotations

import pytest

from quantlab.regimes.registry import (
    RegimeRegistry,
    StateRegistry,
    get_regime_model,
    get_state_variable,
)


@pytest.mark.regime
def test_identity_changes_when_formula_changes() -> None:
    base = get_regime_model("vol_tercile")
    changed = base.model_copy(update={"version": "2", "n_regimes": 4})
    assert changed.identity_hash() != base.identity_hash()
    state = get_state_variable("realized_vol_20")
    state_changed = state.model_copy(update={"lookback": 40, "version": "2"})
    assert state_changed.identity_hash() != state.identity_hash()


@pytest.mark.regime
def test_registry_refuses_overwrite() -> None:
    models = RegimeRegistry()
    with pytest.raises(ValueError, match="cannot overwrite"):
        models.register(get_regime_model("vol_tercile"))
    states = StateRegistry()
    with pytest.raises(ValueError, match="cannot overwrite"):
        states.register(get_state_variable("realized_vol_20"))


@pytest.mark.regime
def test_not_tested_seeds_exist() -> None:
    nifty = get_state_variable("index_nifty_return")
    adv = get_state_variable("liquidity_adv")
    assert "NOT_TESTED" in nifty.mathematical_definition
    assert "NOT_TESTED" in adv.mathematical_definition
    assert "nifty" in nifty.notes.lower()
