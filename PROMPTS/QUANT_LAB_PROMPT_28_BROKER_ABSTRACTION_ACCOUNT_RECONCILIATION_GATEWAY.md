# QUANT LAB — PROMPT 28
# Institutional Broker Abstraction, Account Connectivity & Reconciliation Gateway

**Target Version:** 2.8.0  
**Scope:** Broker-neutral connectivity boundary and account reconciliation infrastructure  
**Critical Rule:** Read-only first. No autonomous order routing.

---

## 1. Mission

Build the institutional **Broker Abstraction & Reconciliation Gateway** that provides a controlled interface between QUANT LAB and external brokerage infrastructure.

The engine must answer:

> **What is the authoritative external account state, how does it reconcile with QUANT LAB's internal state, and can broker connectivity be established without weakening the safety architecture?**

Prompt 28 is a connectivity and reconciliation layer.

It is not:
- a strategy engine
- a portfolio optimizer
- an alpha engine
- a research engine
- a certification engine
- an autonomous trader
- an unrestricted OMS

---

## 2. Safety Boundary

Default and development state:

```text
LIVE_TRADING=false
BROKER_WRITE_ENABLED=false
```

Prompt 28 must initially support **read-only broker connectivity only**.

Required modes:

```text
DISCONNECTED
CONNECTING
CONNECTED_READ_ONLY
DEGRADED
STALE
RECONCILIATION_REQUIRED
BLOCKED
```

Do not implement live order placement as part of the default Prompt 28 path.

Any future write capability must be a separately gated architectural layer.

---

## 3. Broker-Neutral Architecture

Implement a protocol-based adapter model.

```text
QUANT LAB
   │
   ▼
┌─────────────────────────────┐
│ Broker Gateway              │
│                             │
│ Adapter Protocol            │
│ Credential Boundary         │
│ Account Snapshot            │
│ Market Session State        │
│ Orders Read                 │
│ Fills Read                  │
│ Positions Read              │
│ Holdings Read               │
│ Margins Read                │
│ Reconciliation              │
│ Audit                       │
└─────────────┬───────────────┘
              │
      Broker Adapter
              │
      ┌───────┴────────┐
      ▼                ▼
   Zerodha          Future Broker
```

The core must never depend on one broker SDK.

---

## 4. Package

Create:

```text
quantlab.broker_gateway
```

Keep:

```text
__init__.py
```

thin.

No strategy imports.

No alpha imports.

No portfolio-construction imports.

No GP/model imports.

No UI computation.

---

## 5. Adapter Protocol

Define a strict broker-neutral interface.

Conceptually:

```text
connect()
disconnect()
health()
account()
positions()
holdings()
margins()
orders()
fills()
trades()
instrument_metadata()
session_status()
```

Every response must include provenance.

No adapter may silently transform broker data into research data.

---

## 6. Account State

Define immutable snapshots:

```text
BrokerAccountSnapshot
BrokerPositionSnapshot
BrokerHoldingSnapshot
BrokerMarginSnapshot
BrokerOrderSnapshot
BrokerFillSnapshot
```

Each snapshot requires:

```text
broker
account_id_hash
captured_at
source_timestamp
snapshot_id
source_sequence
schema_version
payload_hash
```

Never log secrets.

Never store raw credentials in research records.

---

## 7. Account Identity

Separate:

```text
internal_account_id
broker_account_id
broker_identity
paper_account_id
```

Never assume they are interchangeable.

Broker account identifiers should be protected/redacted where appropriate.

A mismatch must produce:

```text
ACCOUNT_IDENTITY_MISMATCH
```

and block reconciliation.

---

## 8. Read-Only Data Contract

Initial broker gateway must expose:

### Account

- available cash
- collateral
- utilized margin
- available margin
- equity where provided
- buying power where provided

### Positions

- symbol/instrument identity
- exchange
- quantity
- average price
- last price if supplied
- realized P&L if supplied
- unrealized P&L if supplied
- product/type
- timestamp

### Holdings

- quantity
- average cost
- exchange
- instrument identity

### Orders

Read only:

- broker order ID
- status
- side
- quantity
- filled quantity
- pending quantity
- order type
- price
- timestamp
- rejection reason where supplied

### Fills

Read only:

- broker fill/trade ID
- order ID
- quantity
- price
- timestamp
- exchange
- charges where supplied

---

## 9. Instrument Identity

Never use ticker strings as authoritative identity.

Integrate with the Prompt 20 security-master concepts.

Required mapping:

```text
broker_instrument_id
security_id
exchange
trading_symbol
display_symbol
effective_from
effective_to
mapping_source
mapping_confidence
```

Ambiguous mapping must fail closed.

Never silently map:

```text
symbol → security_id
```

when multiple candidates exist.

---

## 10. Broker Clock & Timestamp Discipline

Preserve:
- broker timestamp
- exchange timestamp if supplied
- gateway receipt timestamp
- normalized timestamp

Never overwrite source timestamps.

Clock anomalies must produce a warning or blocking state depending on severity.

---

## 11. Reconciliation Engine

Implement three-way reconciliation:

```text
BROKER STATE
     ↕
GATEWAY SNAPSHOT
     ↕
QUANT LAB INTERNAL STATE
```

Reconcile:

```text
cash
positions
holdings
orders
fills
trades
margins
instrument identity
```

Differences must be explicit.

Result states:

```text
RECONCILED
PARTIAL
MISMATCH
RECONCILIATION_REQUIRED
BLOCKED
```

Never silently repair discrepancies.

---

## 12. Position Reconciliation

For each instrument compare:

```text
broker_qty
internal_qty
delta_qty
broker_avg_price
internal_avg_price
valuation_difference
```

Do not assume average-price semantics are identical between broker and internal accounting.

If semantics differ:

```text
ACCOUNTING_SEMANTICS_UNKNOWN
```

must be raised.

---

## 13. Cash Reconciliation

Compare:

```text
broker_cash
internal_cash
reserved_cash
margin
collateral
unsettled_amounts
```

Cash identity must be explicit.

Unknown settlement or collateral semantics must remain `NOT_TESTED`.

---

## 14. Order Reconciliation

Reconcile broker orders against internal order records.

Detect:

```text
unknown_broker_order
missing_broker_order
duplicate_broker_order
status_mismatch
quantity_mismatch
side_mismatch
instrument_mismatch
timestamp_anomaly
orphan_fill
```

Never invent an internal order to hide an unknown broker order.

Unknown external orders must block any future write-capable path.

---

## 15. Fill Reconciliation

Reconcile:

```text
broker_fill
internal_fill
order_id
quantity
price
timestamp
instrument
```

Detect:

```text
duplicate_fill
missing_fill
orphan_fill
price_mismatch
quantity_mismatch
order_link_break
```

A reconciliation break is a first-class event.

---

## 16. Idempotency

Repeated broker snapshots must not create duplicate state.

Use deterministic identity based on broker-native identifiers where available.

Fallback identity must include enough source information to avoid collision.

Duplicate external event:

```text
same identity + same payload → idempotent
same identity + different payload → integrity failure
```

---

## 17. Event Ordering

Broker events can arrive:
- delayed
- duplicated
- out of order
- partially
- after reconnect

Implement sequence-aware ingestion.

Do not assume receipt order equals market/order chronology.

Where broker sequence information is unavailable, mark ordering limitations explicitly.

---

## 18. Connection Lifecycle

Implement:

```text
DISCONNECTED
   ↓
CONNECTING
   ↓
CONNECTED_READ_ONLY
   ↓
DEGRADED
   ↓
STALE
   ↓
RECONCILIATION_REQUIRED
   ↓
CONNECTED_READ_ONLY
```

Reconnect must not silently erase state.

A stale connection must not be treated as healthy.

---

## 19. Secrets Boundary

Credentials must never enter:
- logs
- ledger
- knowledge graph
- error messages
- experiment metadata
- hashes
- UI tables
- telemetry payloads

Support environment/secret-provider abstraction.

Do not hard-code:

```text
API_KEY
API_SECRET
ACCESS_TOKEN
PASSWORD
TOTP_SECRET
```

Use redacted identifiers for diagnostics.

---

## 20. Zerodha Preparation

Create a broker adapter contract capable of supporting:

```text
Zerodha/Kite
```

but preserve broker-neutral core architecture.

The adapter must initially expose:

```text
connect
health
account
positions
holdings
margins
orders
fills/trades
instrument metadata
```

No order placement.

No order modification.

No cancellation.

No automated trading.

The implementation must not assume that one broker's API semantics define the canonical QUANT LAB domain model.

---

## 21. Safety Integration

Integrate with Prompt 25 without bypassing it.

Broker connectivity must never:
- disable kill switches
- change `LIVE_TRADING`
- change capital limits
- change certification state
- authorize itself
- promote itself
- bypass reconciliation

Required rule:

```text
BROKER_CONNECTED ≠ TRADING_AUTHORIZED
```

And:

```text
CERTIFIED ≠ BROKER_WRITE_ENABLED
```

---

## 22. Prompt 27 Integration

A broker connection may be considered a **production-readiness evidence source**, but Prompt 28 must not alter certification.

Material broker changes must be able to invalidate/review certification through existing governance mechanisms.

---

## 23. Integrity Flags

Implement:

```text
broker_identity_mismatch
broker_snapshot_mutation
broker_payload_hash_mismatch
duplicate_external_event
external_event_collision
unknown_broker_order
orphan_broker_fill
missing_broker_fill
order_reconciliation_break
position_reconciliation_break
cash_reconciliation_break
margin_reconciliation_break
instrument_mapping_ambiguity
instrument_mapping_mutation
timestamp_integrity_failure
event_ordering_failure
stale_broker_state
credential_exposure
broker_write_attempt
live_mode_confusion
certification_bypass
safety_bypass
```

Unset → `NOT_TESTED`.

Direct violations → `FAIL`.

---

## 24. Audit Ledger

Record:

```text
broker_connection_id
adapter_id
broker
account_snapshot_id
position_snapshot_id
order_snapshot_id
fill_snapshot_id
reconciliation_id
snapshot_hash
reconciliation_hash
gateway_version
timestamp
status
```

Do not store credentials.

Knowledge graph nodes:

```text
BROKER_CONNECTION
ACCOUNT_SNAPSHOT
BROKER_ORDER
BROKER_FILL
BROKER_POSITION
RECONCILIATION
BROKER_INCIDENT
```

---

## 25. CLI

Implement:

```text
quantlab broker list
quantlab broker inspect <id>
quantlab broker health
quantlab broker connect
quantlab broker disconnect
quantlab broker account
quantlab broker positions
quantlab broker holdings
quantlab broker margins
quantlab broker orders
quantlab broker fills
quantlab broker snapshot
quantlab broker reconcile
quantlab broker audit
quantlab broker incidents
quantlab broker mappings
```

Research aliases:

```text
quantlab research broker
quantlab research account-state
quantlab research reconciliation
quantlab research broker-health
quantlab research broker-audit
```

Default commands must remain read-only.

---

## 26. Desktop

Add:

**Broker Gateway Lab**

Display:

```text
Connection Status
Read-Only Status
Broker Identity
Account State
Positions
Holdings
Margins
Orders
Fills
Mapping Health
Reconciliation
Incidents
Last Snapshot
Snapshot Hash
```

UI must never:
- place orders
- modify orders
- cancel orders
- store secrets
- mutate broker snapshots
- bypass reconciliation
- enable live trading

---

## 27. Testing

Implement dedicated tests for:

- adapter protocol
- fake broker adapter
- account snapshots
- position snapshots
- order snapshots
- fill snapshots
- deterministic hashes
- idempotent ingestion
- duplicate event handling
- event ordering
- stale connections
- reconnect
- identity mapping
- ambiguous symbols
- position reconciliation
- cash reconciliation
- order reconciliation
- fill reconciliation
- orphan fills
- unknown broker orders
- credential redaction
- write-attempt rejection
- safety integration
- certification integration
- UI offscreen smoke
- regression across Prompts 01–27

Required:

```text
ruff clean
mypy --strict clean on owned modules
pytest clean
LIVE_TRADING=false
BROKER_WRITE_ENABLED=false
```

---

## 28. Fake Broker Requirement

Before any real broker adapter is enabled, implement a deterministic:

```text
MockBrokerAdapter
```

It must generate controlled scenarios:

```text
normal account
position mismatch
cash mismatch
duplicate fill
orphan fill
unknown order
stale snapshot
out-of-order events
instrument mapping ambiguity
partial data
connection failure
credential failure
```

These scenarios are for infrastructure verification, not market evidence.

---

## 29. Real Broker Adapter Boundary

If a Zerodha/Kite adapter is introduced later:

```text
Zerodha Adapter
      ↓
Broker Gateway
      ↓
Canonical Account State
      ↓
Reconciliation
      ↓
Safety / Certification
```

Never:

```text
Strategy → Zerodha SDK
AI → Zerodha SDK
Portfolio → Zerodha SDK
UI → Zerodha SDK
```

No direct broker calls from research packages.

---

## 30. NOT_TESTED

Do not fabricate:

- broker execution quality
- exchange acknowledgement guarantees
- live market-data quality
- broker outage behavior beyond tested scenarios
- settlement semantics not supplied by broker
- real order-book behavior
- live tax/fee semantics unless sourced
- live write-path safety
- production trading performance

---

## 31. Definition of Done

Prompt 28 is complete only when:

1. Broker access is protocol-based.
2. Core is broker-neutral.
3. Read-only mode is default.
4. Account state is immutable and hashed.
5. Broker identity is explicit.
6. Security-master mapping is controlled.
7. Positions reconcile deterministically.
8. Cash reconciles deterministically.
9. Orders reconcile deterministically.
10. Fills reconcile deterministically.
11. Unknown external state never disappears.
12. Duplicate events are idempotent.
13. Out-of-order events are handled explicitly.
14. Credentials never enter logs or research records.
15. Broker write attempts fail closed.
16. Prompt 25 safety cannot be bypassed.
17. Prompt 27 certification cannot be bypassed.
18. `LIVE_TRADING=false`.
19. `BROKER_WRITE_ENABLED=false`.
20. Full regression remains green.

**Final principle:**

> The broker is an external source of account truth—not an authority over QUANT LAB's research, risk, safety, or governance state.

---

## 32. Deliverables

Create:

```text
src/quantlab/broker_gateway/
src/quantlab/app/broker.py
src/quantlab/ui/pages/broker_gateway_lab.py
tests/broker_gateway/

docs/decisions/ADR-<next-unused>-broker-gateway.md
docs/architecture/BROKER_GATEWAY.md
docs/architecture/BROKER_ABSTRACTION.md
docs/architecture/ACCOUNT_RECONCILIATION.md
docs/research/BROKER_CONNECTIVITY.md
```

Add:

```text
MockBrokerAdapter
BrokerAdapter protocol
canonical broker models
snapshot repository
reconciliation engine
mapping layer
connection state machine
audit layer
```

Update:

```text
README
BACKLOG
LOCAL_RUN
architecture map
health registry
knowledge ingest
ledger schema
desktop navigation
```

Do not rewrite Prompts 01–27.

**Prompt 28 ends at a controlled, read-only broker/account boundary.**
