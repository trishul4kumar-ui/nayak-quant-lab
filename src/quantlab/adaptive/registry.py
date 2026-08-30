"""Append-only adaptive-model registry."""

from __future__ import annotations

from quantlab.adaptive.definition import AdaptiveModelDefinition
from quantlab.adaptive.library import seed_adaptive_models


class AdaptiveRegistry:
    def __init__(self) -> None:
        self._defs: dict[tuple[str, str], AdaptiveModelDefinition] = {}
        for item in seed_adaptive_models():
            self.register(item)

    def register(self, definition: AdaptiveModelDefinition) -> None:
        key = (definition.adaptive_model_id, definition.version)
        if key in self._defs:
            raise ValueError(
                f"cannot overwrite {definition.adaptive_model_id}@"
                f"{definition.version}; bump version"
            )
        self._defs[key] = definition

    def get(
        self, adaptive_model_id: str, version: str | None = None
    ) -> AdaptiveModelDefinition | None:
        if version is not None:
            return self._defs.get((adaptive_model_id, version))
        versions = [
            item for item in self._defs.values() if item.adaptive_model_id == adaptive_model_id
        ]
        if not versions:
            return None
        return versions[-1]

    def list(self) -> list[AdaptiveModelDefinition]:
        return list(self._defs.values())


_MODELS = AdaptiveRegistry()


def get_adaptive_model(
    adaptive_model_id: str, version: str | None = None
) -> AdaptiveModelDefinition:
    found = _MODELS.get(adaptive_model_id, version)
    if found is None:
        raise KeyError(f"unknown adaptive model {adaptive_model_id}")
    return found


def list_adaptive_models() -> list[AdaptiveModelDefinition]:
    return _MODELS.list()


def default_adaptive_registry() -> AdaptiveRegistry:
    return _MODELS
