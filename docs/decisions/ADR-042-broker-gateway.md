# ADR-042 — Broker Abstraction, Account Connectivity & Reconciliation Gateway

## Context
Prompt 28 asked for a broker-neutral, read-only account connectivity and reconciliation gateway. ADR-007 already defines the original `quantlab.brokers` paper protocol with `place_order`. Desktop nav `broker` is the existing Broker Console wizard. Health already registers an optional `broker_gateway` component.

## Decision
Add `quantlab.broker_gateway` as a read-only adapter/reconciliation layer. Default adapter is `MockBrokerAdapter`. Vendor adapters remain a not-enabled contract with no SDK import. Top-level CLI is `quantlab broker`. Desktop nav key is `gateway` (**Broker Gateway Lab**), distinct from `broker`.

`BROKER_WRITE_ENABLED=false`. `LIVE_TRADING=false`. `BROKER_CONNECTED ≠ TRADING_AUTHORIZED`. Unknown broker orders and orphan fills are retained and never silently repaired.

## Consequences
- `quantlab.brokers` remains the original paper stub
- Broker Console (`broker`) remains a separate wizard
- Connectivity cannot disable kill switches, change certification, or enable live
- Real vendor SDKs are out of scope for this ADR
