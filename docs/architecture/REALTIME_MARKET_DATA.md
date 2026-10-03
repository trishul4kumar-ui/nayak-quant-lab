# Real-Time Market Data & State Gateway

**Version:** 3.1.0  
**Package:** `quantlab.realtime_data`  
**Desktop:** Real-Time Data Lab (`rt_data`)  
**CLI:** `quantlab realtime`

Observe-only production-time counterpart to the Prompt 20 fabric. Default adapter: `MockMarketDataAdapter`.
An optional `KiteMarketDataAdapter` uses Kite Connect v3's REST quote endpoint
only when local environment configuration supplies explicit exchange-scoped
symbols. It has no vendor order client or write transport.

```text
LIVE_TRADING=false
BROKER_WRITE_ENABLED=false
REAL-TIME OBSERVATION ≠ TRADING
CONNECTED ≠ HEALTHY
```

Frozen snapshots are immutable. Stale/invalid/missing never silently become valid. Vendor SDKs are not imported.

`/quote` is a point-in-time REST snapshot and does not provide a market-event
sequence. The adapter records that limitation as `sequence_guarantee=not_provided`;
it never invents sequence numbers or claims stream-level gap detection. A later
WebSocket adapter must provide its own explicit sequence/provenance semantics.
