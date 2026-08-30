# ADR-032 — Institutional Paper OMS

## Context
Prompt 18 asks QUANT LAB to answer: given an immutable investment decision and target portfolio, what orders would be required, how those orders transition through an OMS lifecycle, what would fill under paper execution assumptions, what positions and cash would result, and whether that state reconciles with the recorded order/fill history — without connecting to a live broker.

Prompts 01–17 already own the PIT fabric, canonical next-bar backtester, research gate, Prompt 13 microstructure simulation, Prompt 17 capital decisions, JSONL ledger, and knowledge graph. A second copy of any of those would fork scientific identity.

## Problem
Without an explicit paper OMS, target portfolios look like live tickets, simulated fills look like broker confirmations, cash is silently equated with portfolio value, duplicate submissions create duplicate orders, and a future broker adapter can be reached accidentally.

## Options
1. Extend `quantlab.execution.ExecutionEngine` until it places paper and live orders
2. Add `quantlab.paper_oms` as a paper-only lifecycle, accounting, and reconciliation engine that consumes Prompt 17 targets and Prompt 13 fills
3. Wait for a live Zerodha adapter and fold paper into the broker path

## Decision
Option 2.

1. Paper OMS is the controlled boundary after `TargetPortfolio`. It produces `OrderIntent`, `OrderPlan`, `PaperOrder`, `PaperFill`, paper positions, cash, and `ReconciliationReport`.
2. `quantlab.execution_research.OrderIntent` remains Prompt 13's research object. Paper OMS `OrderIntent` is a different type in `quantlab.paper_oms`.
3. `quantlab.backtest.run_backtest` remains the only research P&L engine. Paper OMS does not become a second backtester.
4. Prompt 13 remains the only source of spread, slippage, impact, latency, and partial-fill formulas. Paper OMS calls `simulate_fill`.
5. Prompt 05 remains the only research gate. Prompt 17 remains authoritative for allocation. Paper OMS must not silently resize a target.
6. Lifecycle transitions are a state machine. Invalid transitions raise `InvalidOrderTransition`.
7. Idempotency is mandatory. The same decision + account + snapshot + policy + plan returns the existing run.
8. Partial fills and residuals are first-class. `requested = filled + remaining + cancelled + expired`.
9. Cash and equity identities are FAIL, not warnings. Reconciliation never silently repairs a break.
10. Paper fills are never labelled broker-confirmed or live-filled.
11. `LIVE_TRADING` remains false. Broker SDKs, credentials, and live adapters are prohibited in `quantlab.paper_oms`.
12. A future-neutral `BrokerAdapter` protocol may exist; Prompt 18 instantiates only `PaperExecutionAdapter`.
13. Official NSE holidays, Indian tax schedules, and corporate-action adjustments remain `NOT_TESTED` when unknown.
14. Failed orders and reconciliation breaks are retained in the ledger and knowledge graph.

## Consequences
- `TARGET ≠ INTENT ≠ PLAN ≠ PAPER ORDER ≠ PAPER FILL ≠ POSITION ≠ BROKER CONFIRMATION`
- Integrity gains paper-OMS flags; `pre_arrival_fill`, `future_liquidity_leak`, `full_fill_assumption`, `hidden_partial_fill`, and `decision_hash_mismatch` are reused, not duplicated.
- Desktop Paper OMS Lab is a query/controller of `quantlab.app.paper_oms`. Buttons are `SUBMIT PAPER`, never `PLACE LIVE ORDER`.
- `quantlab portfolio` remains Prompt 07. `quantlab capital` remains Prompt 17. Paper CLI is `quantlab paper …`.

## References
Prompt 18; ADR-021, ADR-027, ADR-031
