# Real-Time Market Data & State Gateway

**Version:** 3.1.0  
**Package:** `quantlab.realtime_data`  
**Desktop:** Real-Time Data Lab (`rt_data`)  
**CLI:** `quantlab realtime`

Observe-only production-time counterpart to the Prompt 20 fabric. Default adapter: `MockMarketDataAdapter`.

```text
LIVE_TRADING=false
BROKER_WRITE_ENABLED=false
REAL-TIME OBSERVATION ≠ TRADING
CONNECTED ≠ HEALTHY
```

Frozen snapshots are immutable. Stale/invalid/missing never silently become valid. Vendor SDKs are not imported.
