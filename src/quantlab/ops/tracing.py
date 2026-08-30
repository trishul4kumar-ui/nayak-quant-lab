"""Tracing stubs. No broker spans."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def span(name: str) -> Iterator[str]:
    yield name
