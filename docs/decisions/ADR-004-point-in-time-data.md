# ADR-004 — Point-in-time data

## Context
Qlib includes `qlib/data/pit.py`. Look-ahead is the main way amateur backtests lie.

## Problem
Bars, fundamentals, and news have different “when did this exist?” times.

## Options
1. Use only `datetime` index (pandas)
2. Four timestamps on every market object: event, effective, available, ingestion
3. Defer PIT until fundamentals exist

## Decision
Option 2 on Day 1 for bars, even if all four times are equal on synthetic data. Integrity checks refuse features that use `available_time > as_of`.

## Consequences
- Slightly more verbose domain objects
- Future fundamental adapters cannot silently use restatements

## References
Qlib PIT; TradingAgents look-ahead filtering notes
