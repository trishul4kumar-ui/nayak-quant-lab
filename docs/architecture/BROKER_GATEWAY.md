# Broker Gateway

**Version:** 3.1.0
**Package:** `quantlab.broker_gateway`  
**Desktop:** Broker Gateway Lab (`gateway`)

Read-only account connectivity and reconciliation. The desktop Broker Gateway Lab offers
an explicit choice between `MockBrokerAdapter` and the environment-configured Kite observer.
Kite uses only a fixed allowlist of authenticated GET endpoints: profile, margins, positions,
holdings, orders, trades, and instruments. It cannot form an order request.

```text
LIVE_TRADING=false
BROKER_WRITE_ENABLED=false
BROKER_CONNECTED ≠ TRADING_AUTHORIZED
```

Write/order paths raise `BrokerWriteError`. Credentials are redacted. Snapshots are immutable and hashed. Vendor SDKs are not imported.

The desktop connection button verifies the Kite profile endpoint only. **Refresh snapshot**
collects the account observation and **Reconcile** compares it with local books; neither
operation sends, modifies, or cancels an order. A token failure is reported in the active
workspace and does not modify broker state.
