# ADR-043 — Real-Time Market Data & State Gateway

## Context
Prompt 29 asked for an observe-only production-time counterpart to the Prompt 20 PIT fabric. ADR-041 already names live-trading certification. This ADR is therefore **043**.

Desktop nav `data` remains the historical fabric. CLI `quantlab realtime` must not steal `quantlab data`.

## Decision
Add `quantlab.realtime_data` as an observe-only market-data gateway. Default adapter is `MockMarketDataAdapter`, plus `ReplayMarketDataAdapter`. Production vendor adapters are out of scope. Frozen `RealTimeSnapshot` / `MarketState(T)` cannot be mutated by future appends.

```text
LIVE_TRADING = FALSE
BROKER_WRITE_ENABLED = FALSE
REAL-TIME OBSERVATION ≠ TRADING
CONNECTED ≠ HEALTHY
FRESH ≠ VALID
```

Time fields stay distinct: `event_time`, `exchange_time`, `source_time`, `receive_time`, `processing_time`, `decision_time`.

Top-level CLI is `quantlab realtime`. Desktop nav key is `rt_data` (**Real-Time Data Lab**).

## Consequences
- Prompt 20 fabric remains the historical PIT store
- Stale/invalid/missing never silently become valid
- Sequence gaps, duplicates, and out-of-order ticks are classified
- Qt does not parse streams or mutate snapshots
