"""Append-only execution-research model registry."""

from __future__ import annotations

from quantlab.execution_research.definition import MarketMicrostructureDefinition
from quantlab.execution_research.library import seed_execution_models


class ExecutionRegistry:
    def __init__(self) -> None:
        self._defs: dict[tuple[str, str], MarketMicrostructureDefinition] = {}
        for item in seed_execution_models():
            self.register(item)

    def register(self, definition: MarketMicrostructureDefinition) -> None:
        key = (definition.definition_id, definition.version)
        if key in self._defs:
            raise ValueError(
                f"cannot overwrite {definition.definition_id}@{definition.version}; bump version"
            )
        self._defs[key] = definition

    def get(
        self, definition_id: str, version: str | None = None
    ) -> MarketMicrostructureDefinition | None:
        if version is not None:
            return self._defs.get((definition_id, version))
        versions = [item for item in self._defs.values() if item.definition_id == definition_id]
        if not versions:
            return None
        return versions[-1]

    def list(self) -> list[MarketMicrostructureDefinition]:
        return list(self._defs.values())


_MODELS = ExecutionRegistry()


def get_execution_model(
    definition_id: str, version: str | None = None
) -> MarketMicrostructureDefinition:
    found = _MODELS.get(definition_id, version)
    if found is None:
        raise KeyError(f"unknown execution model {definition_id}")
    return found


def list_execution_models() -> list[MarketMicrostructureDefinition]:
    return _MODELS.list()


def default_execution_registry() -> ExecutionRegistry:
    return _MODELS
