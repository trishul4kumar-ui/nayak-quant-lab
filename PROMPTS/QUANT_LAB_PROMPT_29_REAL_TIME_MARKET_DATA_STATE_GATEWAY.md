# QUANT LAB — PROMPT 29
# Institutional Real-Time Market Data & State Gateway

**Target Version:** 2.9.0  
**Primary Package:** `quantlab.realtime_data`  
**ADR:** ADR-041  
**Safety:** OBSERVE-ONLY — NO ORDER ROUTING

## Mission

Build the production-time counterpart to Prompt 20's Point-in-Time Data Fabric.

The engine answers:

> What market information was actually observable to QUANT LAB at time T, when did it arrive, was it valid and fresh, and what deterministic `MarketState` / `StateSnapshot` could legitimately be constructed?

### Non-negotiable boundaries

```text
REAL-TIME OBSERVATION ≠ TRADING
REAL-TIME STATE ≠ SIGNAL
ARRIVAL TIME ≠ EVENT TIME
CONNECTED ≠ HEALTHY
FRESH ≠ VALID
```

Prompt 29 must not place/modify/cancel orders, import broker SDKs, construct portfolios, fabricate missing data, use future observations, or become a second data fabric.

## Architecture

```text
Prompt 20 PIT / Production Data Fabric
              │
              ▼
       Prompt 29 Data Gateway
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
 ingestion  quality  freshness
    │         │         │
    └─────────┼─────────┘
              ▼
       Frozen StateSnapshot(T)
              │
              ▼
       Prompt 30 Decision Engine
```

Reuse Prompt 20's security master, provenance, calendar and identity systems.

## Time Model

Every observation must distinguish where available:

- `event_time`
- `exchange_time`
- `source_time`
- `receive_time`
- `processing_time`
- `decision_time`

Never assume they are equivalent.

A valid observation must satisfy the applicable source timestamp contract. Unknown ordering is explicit `NOT_TESTED`, never fabricated.

## Immutable Observation Contract

Create a typed observation containing:

- `observation_id`
- `security_id`
- venue/source
- event/receive/processing timestamps
- sequence number when available
- price/quantity/volume
- bid/ask when available
- provenance
- schema version
- payload hash
- quality status
- freshness status
- correction status

Raw payloads are immutable. Normalized records retain raw lineage.

## Provider Architecture

```text
MarketDataAdapter
 ├── MockMarketDataAdapter
 └── ReplayMarketDataAdapter
```

Production vendor adapters are out of scope for this prompt. No `kiteconnect`, Zerodha, OpenAlgo, broker or OMS imports.

## Quality Engine

Check:

- schema
- timestamps
- monotonicity
- sequence gaps
- duplicates
- out-of-order events
- impossible prices
- negative quantity/volume
- stale data
- crossed/locked quotes
- abnormal jumps
- disconnect/heartbeat
- clock drift
- session mismatch
- security mapping

States:

```text
VALID | DEGRADED | STALE | INVALID | MISSING | DISCONNECTED | UNKNOWN
```

Never silently convert stale/invalid/missing data into valid data.

## Freshness

Implement field-specific freshness policies for price, volume, quotes and reference data.

A stale value must remain explicitly stale or unavailable. No silent forward-fill.

## Sequence / Replay Integrity

```text
N → N+1       VALID
N → N+2       GAP
N+2 → N+1     OUT_OF_ORDER
N → N         DUPLICATE
```

Gaps and corrections remain visible.

## Market Session

Reuse Prompt 20 calendar infrastructure.

States:

```text
PRE_OPEN | OPEN | CLOSING | CLOSED | HALTED | UNKNOWN
```

Do not invent official NSE/BSE holidays.

## Real-Time State

Construct `MarketState(T)` and cross-sectional `StateSnapshot(T)` only from information available by T.

Missing fields remain `None`/unavailable.

Once frozen, `StateSnapshot(T)` is immutable.

Required property:

```text
append_future_data(snapshot_T) == snapshot_T
```

## Snapshot Identity

Every snapshot contains:

```text
snapshot_id
snapshot_hash
source_manifest_hash
security_master_hash
calendar_version
schema_version
```

Identical observations and configuration must produce identical hashes.

## Health

Expose:

```text
feed_connected
last_observation_time
observation_age
sequence_health
clock_health
data_quality
session_state
security_mapping_health
snapshot_health
```

Overall states:

```text
HEALTHY | DEGRADED | STALE | HALTED | DISCONNECTED | UNKNOWN
```

`UNKNOWN` is never healthy.

## CLI

```bash
quantlab realtime health
quantlab realtime status
quantlab realtime sources
quantlab realtime start
quantlab realtime stop
quantlab realtime snapshot
quantlab realtime inspect
quantlab realtime quality
quantlab realtime freshness
quantlab realtime sequence
quantlab realtime clock
quantlab realtime session
quantlab realtime replay
quantlab realtime audit
```

No command may route orders.

## Desktop

Create **Real-Time Data Lab** as a `quantlab.app` query/view layer.

Display feed health, freshness, sequence health, clock, session, security mapping, snapshots and incidents.

Qt does not parse streams, mutate snapshots, access broker credentials or execute.

## Integrity Flags

At minimum:

```text
future_market_observation
future_state_mutation
future_volume
future_quote
future_reference_data
timestamp_order_violation
receive_time_violation
sequence_gap_hidden
duplicate_observation
stale_data_used
invalid_data_used
missing_data_filled
clock_drift
session_mismatch
security_identity_mismatch
snapshot_mutation
realtime_replay_mismatch
```

`None → NOT_TESTED`; direct leakage → `FAIL`.

## Testing

Include unit, property, integration and offscreen UI tests for timestamp ordering, future isolation, stale data, gaps, duplicates, malformed events, clock drift, session transitions, identity mapping, immutability, deterministic hashes, replay, disconnect/reconnect and degraded feeds.

## NOT_TESTED

Do not fabricate official exchange holidays, production feed certification, institutional multicast guarantees, order-book depth, broker-feed reliability, calibrated tick liquidity, or real-time corporate-action dissemination guarantees.

## Acceptance

Prompt 29 is complete only when the real-time observation path is deterministic, auditable, immutable, health-aware and completely isolated from broker execution.

```text
LIVE_TRADING = false
BROKER_WRITE_ENABLED = false
NO BROKER IMPORTS
NO ORDER PATH
```
