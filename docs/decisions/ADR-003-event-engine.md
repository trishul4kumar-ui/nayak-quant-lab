# ADR-003 — Event engine

## Context
VN.Py uses a queue EventEngine. Hummingbot is asyncio. QuantDinger isolates trading in a worker.

## Problem
Need a clock and event types without overbuilding.

## Options
1. Full async engine Day 1
2. In-process synchronous EventBus + injected Clock
3. No events; only DataFrames

## Decision
Option 2. Typed events exist; the Day 1 backtester is bar-driven and deterministic. The bus is for future live/paper.

## Consequences
- Tests are deterministic
- Live worker can subscribe later without changing domain events

## References
VN.Py `vnpy/event/engine.py`
