from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quantlab.discovery.definitions import NoveltyClass
from quantlab.discovery.expression import feature_node, unary
from quantlab.discovery.novelty import novelty_class


@pytest.mark.discovery
def test_identical_panel_is_duplicate() -> None:
    ts = datetime(2024, 1, 2, tzinfo=UTC)
    panel = {ts: {"A": 1.0, "B": 2.0, "C": 3.0}}
    expr = unary("rank", feature_node("momentum_20"))
    klass, corr = novelty_class(expr, panel, {"ref": panel}, [ts], set())
    assert klass is NoveltyClass.DUPLICATE
    assert corr >= 0.99
