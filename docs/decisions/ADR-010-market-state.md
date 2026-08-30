# ADR-010 — MarketState

## Context
Prompt 02 forbids every strategy from independently re-parsing raw OHLCV. Qlib datasets and VN.Py bars are lower-level.

## Problem
Need a canonical as-of representation (price, vol, liquidity, trend) that respects PIT.

## Options
1. Strategies keep reading bars only
2. MarketState built from bars available at T; features hang off it
3. Full order-book state on Day 1

## Decision
Option 2. Microstructure fields exist as optional stubs.

## Consequences
- StrategyContext carries `market_states`
- Momentum slice uses `features["momentum_N"]` when present

Prompt 09 market-level observables live on `StateSnapshot` (ADR-023). This ADR’s per-instrument `MarketState` is unchanged.
