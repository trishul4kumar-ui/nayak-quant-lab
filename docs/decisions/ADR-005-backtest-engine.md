# ADR-005 — Backtest engine

## Context
Naïve loops fill at the same close used for the signal. Qlib and Lumibot separate signal time from fill time.

## Problem
First engine must be honest enough to validate architecture, not maximize Sharpe.

## Options
1. Vectorized close-to-close with same-bar fill
2. Signal at `t`, return from `t` → `t+1`, costs on turnover
3. Full L2 matching engine

## Decision
Option 2 for Day 1. Document as optimistic vs live (no latency). Partial fills and latency are Phase 5.

## Consequences
- Vertical slice is reproducible and leakage-aware
- Not a production F&O simulator yet

## References
Qlib `qlib/backtest`; Lumibot backtest/live equivalence
