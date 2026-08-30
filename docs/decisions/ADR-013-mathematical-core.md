# ADR-013 — Mathematical core

## Context
Prompt 02 requires broker-independent math. NumPy is already a dependency.

## Problem
Sharpe/drawdown should not be reimplemented inside the backtester, UI, or notebooks.

## Options
1. Copy formulas into the backtest module
2. `quantlab.math` primitives with tests
3. Depend on a large quant library

## Decision
Option 2. Small deterministic functions; SciPy not added yet.

## Consequences
- Backtest analytics call math, not the reverse
- Annualization lives in `quantlab.math.annualization` (ADR-019). Do not scatter `sqrt(252)`.
