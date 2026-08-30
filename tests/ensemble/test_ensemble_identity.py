"""Combination-ensemble identity is hashed; overwrites are refused."""

from __future__ import annotations

import pytest

from quantlab.ensemble.definition import ComponentType, EnsembleComponent, EnsembleDefinition
from quantlab.ensemble.registry import EnsembleRegistry, get_ensemble, list_ensembles


@pytest.mark.ensemble
def test_seed_ensembles_are_registered() -> None:
    ids = {item.ensemble_id for item in list_ensembles()}
    assert "ew_mom_5_20" in ids
    assert "static_ic_mom" in ids
    assert "corr_mom" in ids
    assert "ridge_stack_mom" in ids
    assert "meta_ols_mom" in ids
    assert "hetero_alpha_ols" in ids
    assert get_ensemble("ew_mom_5_20").identity_hash()


@pytest.mark.ensemble
def test_identity_changes_when_window_changes() -> None:
    base = get_ensemble("roll_ic_mom")
    changed = base.model_copy(update={"version": "2", "training_window": 40})
    assert changed.identity_hash() != base.identity_hash()


@pytest.mark.ensemble
def test_registry_refuses_overwrite() -> None:
    registry = EnsembleRegistry()
    with pytest.raises(ValueError, match="overwrite"):
        registry.register(get_ensemble("ew_mom_5_20"))


@pytest.mark.ensemble
def test_empty_and_duplicate_components_fail() -> None:
    with pytest.raises(Exception, match="empty_components"):
        EnsembleDefinition(
            ensemble_id="empty",
            version="1",
            name="empty",
            components=[],
        )
    dup = EnsembleComponent(component_id="rank_momentum_20", component_type=ComponentType.ALPHA)
    with pytest.raises(Exception, match="duplicate_components"):
        EnsembleDefinition(
            ensemble_id="dup",
            version="1",
            name="dup",
            components=[dup, dup],
        )
