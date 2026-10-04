"""Persisted workspace layouts must be recoverable rather than pathological."""

from __future__ import annotations

from quantlab.ui.responsive import valid_splitter_sizes


def test_splitter_rejects_collapsed_and_invalid_values() -> None:
    assert valid_splitter_sizes([500, 500], 2) == [500, 500]
    assert valid_splitter_sizes([1000, 1], 2) is None
    assert valid_splitter_sizes([0, 100], 2) is None
    assert valid_splitter_sizes([100, 100], 3) is None


def test_splitter_requires_usable_minimums() -> None:
    assert valid_splitter_sizes([23, 900], 2) is None
    assert valid_splitter_sizes("not-a-layout", 2) is None
