"""Live / broker UX helpers — stub-friendly, fail-closed."""

from __future__ import annotations

from typing import Any

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.core.config import LiveSafetyGates

_GATE_LABELS: dict[str, str] = {
    "live_trading": "Live trading armed",
    "live_trading_enabled": "Live trading enabled (env)",
    "broker_connected": "Broker adapter connected",
    "risk_engine_healthy": "Risk engine healthy",
    "strategy_approved": "Strategy approved for live",
    "model_approved": "Model approved for live",
    "data_healthy": "Market data healthy",
    "session_valid": "Broker session valid",
}

_PAPER_DEMO_HOLDINGS: list[dict[str, Any]] = [
    {
        "instrument": "NSE:RELIANCE",
        "weight": 0.22,
        "weight_pct": "22.0%",
        "notional": 220_000,
        "pnl": "—",
        "source": "paper_demo",
    },
    {
        "instrument": "NSE:INFY",
        "weight": 0.18,
        "weight_pct": "18.0%",
        "notional": 180_000,
        "pnl": "—",
        "source": "paper_demo",
    },
    {
        "instrument": "NSE:TCS",
        "weight": 0.15,
        "weight_pct": "15.0%",
        "notional": 150_000,
        "pnl": "—",
        "source": "paper_demo",
    },
    {
        "instrument": "NSE:HDFCBANK",
        "weight": 0.12,
        "weight_pct": "12.0%",
        "notional": 120_000,
        "pnl": "—",
        "source": "paper_demo",
    },
    {
        "instrument": "CASH",
        "weight": 0.33,
        "weight_pct": "33.0%",
        "notional": 330_000,
        "pnl": "—",
        "source": "paper_demo",
    },
]


def live_gate_rows(gates: LiveSafetyGates) -> list[tuple[str, bool]]:
    return [(_GATE_LABELS.get(name, name), bool(getattr(gates, name))) for name in _GATE_LABELS]


def target_holdings(runtime: ApplicationRuntime) -> tuple[list[dict[str, Any]], str]:
    """Research targets or paper demo — never live broker positions."""
    from quantlab.capital.memory import last_result

    result = last_result()
    if result is not None and result.decision.target_weights:
        capital = 1_000_000.0
        rows: list[dict[str, Any]] = []
        for name, weight in sorted(
            result.decision.target_weights.items(),
            key=lambda item: abs(item[1]),
            reverse=True,
        ):
            rows.append(
                {
                    "instrument": name,
                    "weight": weight,
                    "weight_pct": f"{weight:.1%}",
                    "notional": weight * capital,
                    "pnl": "—",
                    "source": "capital_target",
                }
            )
        return rows, "Research target weights from Capital Lab — not live PnL."

    prefs = runtime.ui_settings.current
    if prefs.broker_wizard_complete and prefs.broker_adapter == "paper":
        return list(
            _PAPER_DEMO_HOLDINGS
        ), "Paper adapter demo book — illustrative only, not live PnL."

    return [], ""


def execution_monitor_rows(runtime: ApplicationRuntime) -> tuple[list[list[str]], str]:
    """Simulated fill summary from the last execution experiment."""
    runs = [
        run for run in runtime.ledger.list_runs() if run.selection_stage == "execution_research"
    ]
    if not runs:
        return [], "No execution simulations yet — run quantlab execution simulate."
    run = runs[-1]
    metrics = run.metrics or {}
    n_fills = int(metrics.get("n_fills", 0))
    fill_ratio = metrics.get("mean_fill_ratio")
    total_cost = metrics.get("total_cost")
    model = run.execution_model_id or "—"
    rows: list[list[str]] = [
        ["Summary", "Simulated fills (research)", str(n_fills), str(run.gate_outcome or "—")],
    ]
    if n_fills > 0:
        sample = min(n_fills, 5)
        for i in range(sample):
            rows.append(
                [
                    f"SIM-{i + 1}",
                    model[:12],
                    "simulated",
                    f"fill_ratio={fill_ratio:.2f}" if isinstance(fill_ratio, float) else "—",
                ]
            )
    note = (
        f"Last run: {n_fills} simulated fill(s), cost {total_cost:.2f}"
        if isinstance(total_cost, float)
        else f"Last run recorded {n_fills} simulated fill(s)."
    )
    prefs = runtime.ui_settings.current
    if not prefs.broker_wizard_complete:
        note += " Connect a broker adapter to enable live order monitoring."
    elif not runtime.gates.broker_connected:
        note += " Live OMS path remains stubbed — these are research overlays only."
    return rows, note
