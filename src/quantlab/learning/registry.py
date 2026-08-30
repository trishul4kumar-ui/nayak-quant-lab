"""Append-only statistical-model registry."""

from __future__ import annotations

from quantlab.learning.definition import ModelDefinition
from quantlab.learning.library import seed_models


class ModelRegistry:
    def __init__(self) -> None:
        self._defs: dict[tuple[str, str], ModelDefinition] = {}
        for item in seed_models():
            self.register(item)

    def register(self, definition: ModelDefinition) -> None:
        key = (definition.model_id, definition.version)
        if key in self._defs:
            raise ValueError(
                f"cannot overwrite {definition.model_id}@{definition.version}; bump version"
            )
        self._defs[key] = definition

    def get(self, model_id: str, version: str | None = None) -> ModelDefinition | None:
        if version is not None:
            return self._defs.get((model_id, version))
        versions = [item for item in self._defs.values() if item.model_id == model_id]
        if not versions:
            return None
        return versions[-1]

    def list(self) -> list[ModelDefinition]:
        return list(self._defs.values())


_MODELS = ModelRegistry()


def get_model(model_id: str, version: str | None = None) -> ModelDefinition:
    found = _MODELS.get(model_id, version)
    if found is None:
        raise KeyError(f"unknown statistical model {model_id}")
    return found


def list_models() -> list[ModelDefinition]:
    return _MODELS.list()


def default_model_registry() -> ModelRegistry:
    return _MODELS
