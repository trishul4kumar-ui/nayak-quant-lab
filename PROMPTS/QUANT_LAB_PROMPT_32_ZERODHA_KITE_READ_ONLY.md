# QUANT LAB — PROMPT 32
# Institutional Zerodha/Kite Read-Only Account Integration

**Target Version:** 3.2.0 | **Package:** `quantlab.broker_gateway` extension | **ADR:** ADR-046

## Mission
Implement the first real Zerodha/Kite connectivity layer as a **strictly read-only account adapter**.

```text
ZERODHA CONNECTED ≠ TRADING ENABLED
ACCOUNT DATA ≠ MARKET DATA
BROKER STATE ≠ QUANT LAB STATE
READ ≠ WRITE
```

Mandatory:
```text
LIVE_TRADING=false
BROKER_WRITE_ENABLED=false
```

## Architecture
Extend Prompt 28; do not replace it:

```text
BrokerAdapter
 ├── MockBrokerAdapter
 └── KiteReadOnlyAdapter
```

No strategy, portfolio, capital, risk, paper OMS or live execution code belongs here.

## Read-Only Account Surface
Where supported by the current Kite API contract, implement observation of:
- profile/account metadata
- funds/margins
- holdings
- positions
- open orders
- order history
- trades/fills
- instruments/reference identifiers

Do not assume API fields/endpoints. Validate the current provider contract before implementation.

## Credentials
Support secret references such as:
```text
KITE_API_KEY
KITE_ACCESS_TOKEN
```

Never log or persist API keys, tokens, secrets, authorization headers, passwords or raw credential payloads. Redact credentials from errors, UI, backups and the ledger.

## Authentication State Machine
```text
DISCONNECTED → AUTH_REQUIRED → AUTHENTICATING → CONNECTED
                         ↘ AUTH_EXPIRED / REVOKED / ERROR
```
Fail closed on authentication failure.

## Immutable Broker Snapshot
Create:
```text
BrokerAccountSnapshot(
  snapshot_id,
  broker,
  observed_at,
  funds,
  margins,
  holdings,
  positions,
  open_orders,
  trades,
  source_metadata,
  payload_hash,
  snapshot_hash
)
```

Broker observations must never silently overwrite QUANT LAB's internal books.

## Identity
Use Prompt 20's canonical `security_id`. Broker instruments must resolve through the security master. Unknown/ambiguous mappings remain `UNMAPPED`, never guessed.

## Resilience
Implement explicit timeout, retry/backoff, rate-limit handling, partial-response handling, stale-state detection, circuit breaker and API error classification. No infinite retries.

## Write Firewall
Defense in depth:
1. Read-only adapter exposes only read methods.
2. No write SDK calls.
3. Runtime asserts `LIVE_TRADING=false` and `BROKER_WRITE_ENABLED=false`.
4. Any attempted write raises `BrokerWriteError`.
5. Static audit scans for broker-write paths.

Commands such as place/modify/cancel must deterministically fail.

## CLI
```bash
quantlab broker connect
quantlab broker disconnect
quantlab broker status
quantlab broker profile
quantlab broker funds
quantlab broker margins
quantlab broker holdings
quantlab broker positions
quantlab broker orders
quantlab broker trades
quantlab broker snapshot
quantlab broker health
quantlab broker audit
```

## Desktop
Extend Broker Gateway Lab with redacted account identity, funds, margins, holdings, positions, orders, trades, freshness and adapter health. No write controls.

## Integrity
Add:
```text
broker_credential_exposure
broker_write_attempt
broker_write_path
broker_identity_mismatch
broker_snapshot_mutation
broker_schema_drift
broker_response_partial
broker_stale_state
broker_security_mapping_failure
broker_payload_leak
broker_timestamp_failure
```
`None→NOT_TESTED`; direct safety violations→FAIL.

## Testing
Mock all API responses. Test auth, expiry, timeout, rate limits, malformed/partial responses, schema drift, identity mismatch, mapping failures, deterministic snapshots, credential redaction, write rejection and reconnect behavior. CI must not require real credentials.

## NOT_TESTED
Do not claim production uptime, exchange-quality data, execution equivalence, trading authorization or reconciliation correctness.

## Acceptance
A real Zerodha account can be safely observed while every broker-write path remains structurally impossible.

```text
KITE READ=ALLOWED
KITE WRITE=FORBIDDEN
LIVE_TRADING=false
BROKER_WRITE_ENABLED=false
```
