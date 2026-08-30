# Execution research engine

**Status:** Prompt 13 (2026-08-30) — ADR-027

Package `quantlab.execution_research` overlays microstructure, costs, liquidity, and simulated fills on **existing** portfolio targets. It is not a second backtester and not the OMS (`quantlab.execution`).

```
Portfolio target → Order intent → Execution simulation → Fills → Costs
→ Position residual → Realized execution drag
```

Canonical portfolio P&L remains `run_backtest()` (next-bar fill, ADR-005). This engine decomposes friction around that path.

## Identity

`MarketMicrostructureDefinition` is versioned. Formula or parameter changes require a new `definition_id@version`. `config_hash` includes spread, slip, impact, latency, participation, seed, and `CostSchedule`.

## Honesty

| Input | Status if missing |
|---|---|
| PIT bid/ask | `NOT_TESTED` (no silent 0) |
| Official NSE ADV | `NOT_TESTED` |
| Calibrated impact k | `UNCALIBRATED` |
| India tax table | unspecified 0 with provenance |
| Broker fill | never claimed |

Synthetic bar `volume` is a fixture, not NSE ADV. Capacity ₹1L–₹10Cr scenarios are diagnostics.

## Live safety

Simulated fills never call `ExecutionEngine.submit`. `LIVE_TRADING` remains false.
