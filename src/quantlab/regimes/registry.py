"""Append-only regime and state-variable registries."""

from __future__ import annotations

from quantlab.regimes.definition import RegimeModel, StateVariable
from quantlab.regimes.library import seed_regime_models, seed_state_variables


class StateRegistry:
    def __init__(self) -> None:
        self._defs: dict[tuple[str, str], StateVariable] = {}
        for item in seed_state_variables():
            self.register(item)

    def register(self, definition: StateVariable) -> None:
        key = (definition.variable_id, definition.version)
        if key in self._defs:
            raise ValueError(
                f"cannot overwrite {definition.variable_id}@{definition.version}; bump version"
            )
        self._defs[key] = definition

    def get(self, variable_id: str, version: str | None = None) -> StateVariable | None:
        if version is not None:
            return self._defs.get((variable_id, version))
        versions = [item for item in self._defs.values() if item.variable_id == variable_id]
        if not versions:
            return None
        return versions[-1]

    def list(self) -> list[StateVariable]:
        return list(self._defs.values())


class RegimeRegistry:
    def __init__(self) -> None:
        self._defs: dict[tuple[str, str], RegimeModel] = {}
        for item in seed_regime_models():
            self.register(item)

    def register(self, definition: RegimeModel) -> None:
        key = (definition.regime_model_id, definition.version)
        if key in self._defs:
            raise ValueError(
                f"cannot overwrite {definition.regime_model_id}@{definition.version}; bump version"
            )
        self._defs[key] = definition

    def get(self, regime_model_id: str, version: str | None = None) -> RegimeModel | None:
        if version is not None:
            return self._defs.get((regime_model_id, version))
        versions = [item for item in self._defs.values() if item.regime_model_id == regime_model_id]
        if not versions:
            return None
        return versions[-1]

    def list(self) -> list[RegimeModel]:
        return list(self._defs.values())


_STATES = StateRegistry()
_MODELS = RegimeRegistry()


def get_state_variable(variable_id: str, version: str | None = None) -> StateVariable:
    found = _STATES.get(variable_id, version)
    if found is None:
        raise KeyError(f"unknown state variable {variable_id}")
    return found


def list_state_variables() -> list[StateVariable]:
    return _STATES.list()


def get_regime_model(regime_model_id: str, version: str | None = None) -> RegimeModel:
    found = _MODELS.get(regime_model_id, version)
    if found is None:
        raise KeyError(f"unknown regime model {regime_model_id}")
    return found


def list_regime_models() -> list[RegimeModel]:
    return _MODELS.list()


def default_state_registry() -> StateRegistry:
    return _STATES


def default_regime_registry() -> RegimeRegistry:
    return _MODELS
