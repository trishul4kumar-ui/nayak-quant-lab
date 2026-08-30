# Broker Gateway

**Version:** 2.8.0  
**Package:** `quantlab.broker_gateway`  
**Desktop:** Broker Gateway Lab (`gateway`)

Read-only account connectivity and reconciliation. Default adapter: `MockBrokerAdapter`.

```text
LIVE_TRADING=false
BROKER_WRITE_ENABLED=false
BROKER_CONNECTED ≠ TRADING_AUTHORIZED
```

Write/order paths raise `BrokerWriteError`. Credentials are redacted. Snapshots are immutable and hashed. Vendor SDKs are not imported.
