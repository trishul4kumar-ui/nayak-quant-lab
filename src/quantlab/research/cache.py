"""Deterministic result cache. Keys must include every input that changes the result."""

from __future__ import annotations

from typing import Any


class ResultCache:
    """In-process cache. A hit must never mix configurations."""

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    def get(self, key: str) -> Any | None:
        return self._store.get(key)

    def put(self, key: str, value: Any) -> None:
        if not key:
            raise ValueError("cache key cannot be empty")
        self._store[key] = value

    def __contains__(self, key: object) -> bool:
        return key in self._store
