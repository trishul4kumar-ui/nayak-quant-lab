# QUANT LAB — PROMPT 34
# Institutional Production Market Data Feed Integration & Market-State Certification

**Target Version:** 3.4.0 | **Package:** extension of `quantlab.realtime_data` | **ADR:** ADR-048

## Mission
Extend Prompt 29 from mock/replay infrastructure to production-capable real-market data ingestion while retaining one canonical PIT/realtime data architecture.

Question:

> Can QUANT LAB observe real market data continuously, preserve exact provenance, detect degradation and construct trustworthy state?

## Non-Duplication Rule
```text
ONE PIT DATA FABRIC
ONE REAL-TIME DATA GATEWAY
ONE SECURITY MASTER
ONE PROVENANCE MODEL
```

## Provider Architecture
```text
MarketDataAdapter
 ├── Mock
 ├── Replay
 └── ProductionMarketDataAdapter
```
Vendor details must remain outside strategy code.

## Data Classes
Where available:
```text
TRADES
QUOTES
OHLC
VOLUME
REFERENCE_DATA
CORPORATE_ACTION_EVENTS
```
Every observation retains event/receive/processing time, source, venue, security_id, sequence and payload hash.

## Feed States
```text
DISCONNECTED
CONNECTING
CONNECTED
DEGRADED
STALE
HALTED
RECOVERING
```

## Failover
If multiple sources exist, define explicit primary/secondary priority. Record every source switch. Never silently switch.

## Production Quality
Detect:
- message/packet loss where observable
- sequence gaps
- duplicates
- delayed/out-of-order data
- stale quotes/volume
- crossed/locked quotes
- abnormal spreads/jumps
- missing instruments
- corporate-action discontinuities
- reference-data mismatch
- clock drift

## Latency
Measure:
```text
event→receive
receive→process
process→snapshot
```
Never fabricate unavailable exchange-to-system latency.

## Identity / Corporate Actions / Calendar
Reuse Prompt 20. Unknown instruments are rejected from research state rather than guessed. Corporate-action uncertainty degrades state. Do not invent NSE/BSE holidays.

## Market-State Health
Before Prompt 30 consumes production state, publish:
```text
freshness
coverage
quality
source
clock
sequence
identity
session
corporate_action_state
```
Critical unhealthy state must cause downstream abstention.

## Snapshot Provenance
```text
snapshot_id
snapshot_hash
source_manifest_hash
security_master_version
calendar_version
schema_version
quality_hash
```

## CLI
```bash
quantlab market-data connect
quantlab market-data disconnect
quantlab market-data status
quantlab market-data sources
quantlab market-data health
quantlab market-data latency
quantlab market-data quality
quantlab market-data coverage
quantlab market-data instruments
quantlab market-data snapshot
quantlab market-data audit
quantlab market-data replay
```

## Desktop
Extend Real-Time Data Lab with source health, coverage, latency, failover, quality, session, mappings, corporate actions and provenance. Qt remains query-only.

## Integrity
```text
production_feed_gap
production_feed_failover
future_market_data
market_state_stale
market_state_invalid
sequence_gap_hidden
source_provenance_break
security_mapping_guess
corporate_action_gap
calendar_assumption
clock_drift
latency_fabrication
cross_source_disagreement
snapshot_mutation
```

## Testing
Use recorded fixtures and fault injection. Test connect/disconnect, failover, stale feed, sequence gaps, duplicates, ordering, clock drift, source disagreement, identity failures, corporate actions, sessions, deterministic snapshots and downstream abstention. CI must not depend on live feeds.

## NOT_TESTED
Do not claim exchange certification, institutional latency, complete tick/order-book coverage or calibrated market impact without evidence.

## Acceptance
Real market data must enter the existing gateway with provenance and fail-closed quality controls.

```text
REAL MARKET DATA ≠ VALID MARKET DATA
CONNECTED ≠ HEALTHY
LIVE_TRADING=false
BROKER_WRITE_ENABLED=false
```
