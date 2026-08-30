"""Factor identity is hashed; overwrites are refused."""

from __future__ import annotations

import pytest

from quantlab.factors.definition import FactorDefinition, FactorSource
from quantlab.factors.neutralize import residual_factor_definition
from quantlab.factors.registry import FactorRegistry, get_factor


@pytest.mark.factor
def test_identity_changes_when_formula_changes() -> None:
    base = get_factor("style_momentum_20")
    changed = base.model_copy(
        update={"version": "2", "mathematical_definition": "rank(momentum_20^2)"}
    )
    assert changed.identity_hash() != base.identity_hash()


@pytest.mark.factor
def test_registry_refuses_overwrite() -> None:
    registry = FactorRegistry()
    item = get_factor("style_momentum_20")
    with pytest.raises(ValueError, match="cannot overwrite"):
        registry.register(item)


@pytest.mark.factor
def test_residual_gets_a_new_identity() -> None:
    target = get_factor("style_momentum_20")
    control = get_factor("market_ew_beta")
    residual = residual_factor_definition(target, [control])
    assert residual.factor_id != target.factor_id
    assert residual.source is FactorSource.RESIDUAL
    assert residual.identity_hash() != target.identity_hash()
    assert residual.lineage["residual_of"] == target.factor_id


@pytest.mark.factor
def test_not_implemented_seeds_exist() -> None:
    size = get_factor("size_log_cap")
    assert size.source is FactorSource.NOT_IMPLEMENTED
    assert size.lifecycle.value == "not_tested"
    assert isinstance(size, FactorDefinition)
