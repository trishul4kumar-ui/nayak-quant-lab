"""Deterministic orchestration cache. A hit still records that the candidate was tested."""

from __future__ import annotations

from typing import Any

from quantlab.orchestration.errors import OrchestrationError


class OrchestrationCache:
    def __init__(self) -> None:
        self._store: dict[str, Any] = {}
        self.hits: list[str] = []

    def get(self, key: str) -> Any | None:
        value = self._store.get(key)
        if value is not None:
            self.hits.append(key)
        return value

    def put(self, key: str, value: Any) -> None:
        if not key:
            raise OrchestrationError("cache key cannot be empty")
        self._store[key] = value

    def __contains__(self, key: object) -> bool:
        return key in self._store
