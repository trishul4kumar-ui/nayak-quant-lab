"""Model identity is hashed; overwrites are refused."""

from __future__ import annotations

import pytest

from quantlab.learning.definition import Algorithm, ModelDefinition
from quantlab.learning.registry import ModelRegistry, get_model, list_models


@pytest.mark.learning
def test_seed_models_are_registered() -> None:
    ids = {item.model_id for item in list_models()}
    assert "no_signal" in ids
    assert "alpha_mom20" in ids
    assert "ols_mom" in ids
    assert "ridge_mom" in ids
    assert "rf_mom" in ids
    assert "pca_ols_mom" in ids
    assert get_model("ols_mom").identity_hash()


@pytest.mark.learning
def test_registry_refuses_overwrite() -> None:
    registry = ModelRegistry()
    item = ModelDefinition(
        model_id="unit_only",
        version="1",
        name="unit",
        algorithm=Algorithm.OLS,
        features=["momentum_20"],
    )
    registry.register(item)
    with pytest.raises(ValueError, match="overwrite"):
        registry.register(item)
