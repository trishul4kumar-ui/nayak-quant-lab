"""Controlled execution order. Parallel order must not change recorded results."""

from __future__ import annotations

from collections.abc import Callable, Sequence


def run_isolated[T, R](
    items: Sequence[T],
    fn: Callable[[T], R],
    *,
    order: Sequence[int] | None = None,
) -> list[R]:
    """Run each item independently. `order` permutes execution, not identity."""
    indices = list(order) if order is not None else list(range(len(items)))
    if sorted(indices) != list(range(len(items))):
        indices = list(range(len(items)))
    placed: list[R | None] = [None] * len(items)
    for idx in indices:
        placed[idx] = fn(items[idx])
    return [item for item in placed if item is not None]
