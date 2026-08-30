"""Append-only combination-ensemble registry. Distinct from Prompt 07 AlphaEnsemble."""

from __future__ import annotations

from quantlab.ensemble.definition import EnsembleDefinition
from quantlab.ensemble.library import seed_ensembles


class EnsembleRegistry:
    def __init__(self) -> None:
        self._defs: dict[tuple[str, str], EnsembleDefinition] = {}
        for item in seed_ensembles():
            self.register(item)

    def register(self, definition: EnsembleDefinition) -> None:
        key = (definition.ensemble_id, definition.version)
        if key in self._defs:
            raise ValueError(
                f"cannot overwrite {definition.ensemble_id}@{definition.version}; bump version"
            )
        self._defs[key] = definition

    def get(self, ensemble_id: str, version: str | None = None) -> EnsembleDefinition | None:
        if version is not None:
            return self._defs.get((ensemble_id, version))
        versions = [item for item in self._defs.values() if item.ensemble_id == ensemble_id]
        if not versions:
            return None
        return versions[-1]

    def list(self) -> list[EnsembleDefinition]:
        return list(self._defs.values())


_ENSEMBLES = EnsembleRegistry()


def get_ensemble(ensemble_id: str, version: str | None = None) -> EnsembleDefinition:
    found = _ENSEMBLES.get(ensemble_id, version)
    if found is None:
        raise KeyError(f"unknown combination ensemble {ensemble_id}")
    return found


def list_ensembles() -> list[EnsembleDefinition]:
    return _ENSEMBLES.list()


def default_ensemble_registry() -> EnsembleRegistry:
    return _ENSEMBLES
