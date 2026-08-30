from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.discovery.evaluator import evaluate_expression
from quantlab.discovery.expression import feature_node, unary
from quantlab.features.engine import compute_panel, session_calendar
from quantlab.features.registry import get_feature
from quantlab.research.pipeline import load_synthetic_frame


@pytest.mark.discovery
def test_future_bars_do_not_change_history(tmp_path: Path) -> None:
    short = load_synthetic_frame(
        n_days=40,
        ledger_path=tmp_path / "s.jsonl",
        fabric_root=tmp_path / "s_fabric",
    )
    long = load_synthetic_frame(
        n_days=80,
        ledger_path=tmp_path / "l.jsonl",
        fabric_root=tmp_path / "l_fabric",
    )
    dates_short = session_calendar(short.bars)
    feat = get_feature("momentum_20")
    panel_short = compute_panel(feat, short.bars, as_of_times=dates_short)
    panel_long = compute_panel(feat, long.bars, as_of_times=dates_short)
    assert panel_short
    for ts, row in panel_short.items():
        assert panel_long[ts] == row
    expr = unary("rank", feature_node("momentum_20"))
    ranked_short = evaluate_expression(expr, {"momentum_20": panel_short})
    ranked_long = evaluate_expression(expr, {"momentum_20": panel_long})
    for ts, row in ranked_short.items():
        assert ranked_long[ts] == row
