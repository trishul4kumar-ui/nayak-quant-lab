"""Append-only in-process feature registry. Failed definitions are kept."""

from __future__ import annotations

from quantlab.features.definition import FeatureDefinition
from quantlab.features.library import seed_library


class FeatureRegistry:
    def __init__(self) -> None:
        self._defs: dict[tuple[str, str], FeatureDefinition] = {}
        for item in seed_library():
            self.register(item)

    def register(self, definition: FeatureDefinition) -> None:
        key = (definition.feature_id, definition.version)
        if key in self._defs:
            raise ValueError(
                f"cannot overwrite {definition.feature_id}@{definition.version}; bump version"
            )
        self._defs[key] = definition

    def get(self, feature_id: str, version: str | None = None) -> FeatureDefinition | None:
        if version is not None:
            return self._defs.get((feature_id, version))
        versions = [item for item in self._defs.values() if item.feature_id == feature_id]
        if not versions:
            return None
        return versions[-1]

    def list(self) -> list[FeatureDefinition]:
        return list(self._defs.values())


_DEFAULT = FeatureRegistry()


def default_registry() -> FeatureRegistry:
    return _DEFAULT


def get_feature(feature_id: str, version: str | None = None) -> FeatureDefinition:
    found = _DEFAULT.get(feature_id, version)
    if found is None:
        raise KeyError(f"unknown feature {feature_id}")
    return found


def list_features() -> list[FeatureDefinition]:
    return _DEFAULT.list()
