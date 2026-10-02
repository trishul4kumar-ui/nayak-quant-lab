"""Read-only data helpers for dashboard charts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.math.drawdown import drawdown_series, top_drawdowns
from quantlab.ui.widgets.charts import SERIES_COLORS, ChartSeries

BENCHMARK_COLOR = "#78909c"
BENCHMARK_LABEL = "Cash benchmark"


def load_equity_curve(artifacts_dir: Path, experiment_id: str) -> list[float] | None:
    path = artifacts_dir / experiment_id / "equity.json"
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    equity = payload.get("equity")
    if not isinstance(equity, list) or len(equity) < 2:
        return None
    return [float(x) for x in equity]


def load_risk_exposures(artifacts_dir: Path, experiment_id: str) -> dict[str, float]:
    path = artifacts_dir / experiment_id / "exposure.json"
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    raw = payload.get("exposures")
    if not isinstance(raw, dict):
        return {}
    out: dict[str, float] = {}
    for key, value in raw.items():
        try:
            out[str(key)] = float(value)
        except (TypeError, ValueError):
            continue
    return out


def load_validation_benchmark(artifacts_dir: Path, experiment_id: str) -> dict[str, Any] | None:
    path = artifacts_dir / experiment_id / "validation.json"
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    bench = payload.get("benchmark")
    return bench if isinstance(bench, dict) else None


def rebase_to_one(values: list[float]) -> list[float]:
    if len(values) < 2 or values[0] == 0:
        return list(values)
    base = values[0]
    return [value / base for value in values]


def equity_chart_series(
    equity: list[float],
    *,
    strategy_label: str = "Strategy",
    include_benchmark: bool = True,
    color: str = SERIES_COLORS[0],
) -> list[ChartSeries]:
    if len(equity) < 2:
        return []
    strategy = rebase_to_one(equity)
    series = [ChartSeries(label=strategy_label, values=strategy, color=color)]
    if include_benchmark:
        series.append(
            ChartSeries(
                label=BENCHMARK_LABEL,
                values=[1.0] * len(strategy),
                color=BENCHMARK_COLOR,
                dashed=True,
            )
        )
    return series


def drawdown_episode_rows(equity: list[float], n: int = 5) -> list[list[str]]:
    rows: list[list[str]] = []
    for episode in top_drawdowns(equity, n):
        recovery = "open" if episode.recovery_duration is None else str(episode.recovery_duration)
        rows.append(
            [
                str(episode.peak_index),
                str(episode.trough_index),
                f"{episode.drawdown:.2%}",
                str(episode.duration),
                recovery,
            ]
        )
    return rows


def latest_equity(runtime: ApplicationRuntime) -> tuple[str, list[float]] | None:
    for run in reversed(runtime.ledger.list_runs()):
        curve = load_equity_curve(runtime.paths.artifacts_dir, run.id)
        if curve:
            return run.id, curve
    return None


def equity_for_experiments(
    runtime: ApplicationRuntime, experiment_ids: list[str]
) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    root = runtime.paths.artifacts_dir
    for exp_id in experiment_ids:
        curve = load_equity_curve(root, exp_id)
        if curve:
            out[exp_id] = curve
    return out


def latest_run_metrics(runtime: ApplicationRuntime) -> dict[str, Any] | None:
    runs = runtime.ledger.list_runs()
    if not runs:
        return None
    run = runs[-1]
    return {
        "id": run.id,
        "name": run.name,
        "sharpe": run.metrics.get("sharpe"),
        "total_return": run.metrics.get("total_return"),
        "max_drawdown": run.metrics.get("max_drawdown"),
        "gate_outcome": run.gate_outcome,
        "data_kind": run.data_kind,
    }


def experiment_scatter_points(runtime: ApplicationRuntime) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for row in runtime.ledger.list_runs()[-50:]:
        sharpe = row.metrics.get("sharpe")
        total_return = row.metrics.get("total_return")
        max_dd = row.metrics.get("max_drawdown")
        if sharpe is None or total_return is None:
            continue
        points.append(
            {
                "id": row.id,
                "name": row.name,
                "x": float(sharpe),
                "y": float(total_return),
                "max_drawdown": None if max_dd is None else float(max_dd),
                "gate": row.gate_outcome or "",
            }
        )
    return points


def drawdown_from_equity(equity: list[float]) -> list[float]:
    return drawdown_series(equity)
