"""Append-only factor registry. Formula changes require a new version."""

from __future__ import annotations

from quantlab.factors.definition import FactorDefinition
from quantlab.factors.library import seed_factors


class FactorRegistry:
    def __init__(self) -> None:
        self._defs: dict[tuple[str, str], FactorDefinition] = {}
        for item in seed_factors():
            self.register(item)

    def register(self, definition: FactorDefinition) -> None:
        key = (definition.factor_id, definition.version)
        if key in self._defs:
            raise ValueError(
                f"cannot overwrite {definition.factor_id}@{definition.version}; bump version"
            )
        self._defs[key] = definition

    def get(self, factor_id: str, version: str | None = None) -> FactorDefinition | None:
        if version is not None:
            return self._defs.get((factor_id, version))
        versions = [item for item in self._defs.values() if item.factor_id == factor_id]
        if not versions:
            return None
        return versions[-1]

    def list(self) -> list[FactorDefinition]:
        return list(self._defs.values())


_DEFAULT = FactorRegistry()


def default_registry() -> FactorRegistry:
    return _DEFAULT


def get_factor(factor_id: str, version: str | None = None) -> FactorDefinition:
    found = _DEFAULT.get(factor_id, version)
    if found is None:
        raise KeyError(f"unknown factor {factor_id}")
    return found


def list_factors() -> list[FactorDefinition]:
    return _DEFAULT.list()
