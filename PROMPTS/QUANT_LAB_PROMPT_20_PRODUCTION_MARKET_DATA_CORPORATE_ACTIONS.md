# QUANT LAB — PROMPT 20
# Production Market Data, Corporate Actions, Security Master & Data Quality Engine

**Target release:** QUANT LAB 2.0.0  
**Depends on:** Prompts 01–19  
**Primary objective:** Upgrade the existing PIT data fabric into a production-grade Indian-market data foundation without inventing or silently correcting market history.

## 0. CODING-AGENT DIRECTIVE

This is a foundational infrastructure prompt.

Before writing code:

1. Inspect Prompts 01–19.
2. Inspect `quantlab.data`, identity, calendar, universe, catalog, PIT queries, Parquet/DuckDB interfaces, integrity framework, ledger, Knowledge Graph, CLI, app layer and UI.
3. Preserve the existing PIT contract:
   `available_time <= as_of`.
4. Do not replace the data fabric.
5. Extend it into a production-grade source/provenance/quality layer.
6. Never invent NSE/BSE prices, holidays, corporate actions, symbols or fundamentals.
7. User-supplied/licensed data must retain its source identity and checksum.

**No broker integration in Prompt 20.**

## 1. CORE QUESTION

The engine must answer:

> **What market information existed, in what exact form, for which security, and was it actually available to research at time T?**

The system must distinguish:

```text
EVENT_TIME
vs
ANNOUNCEMENT_TIME
vs
EFFECTIVE_TIME
vs
AVAILABLE_TIME
vs
INGEST_TIME
```

The earliest legitimate research availability must control PIT access.

## 2. ARCHITECTURE

```text
SOURCE
  ↓
RAW IMMUTABLE OBJECT
  ↓
SHA-256 / PROVENANCE
  ↓
CATALOG
  ↓
SCHEMA VALIDATION
  ↓
SECURITY MASTER
  ↓
SYMBOL / IDENTITY HISTORY
  ↓
CORPORATE ACTIONS
  ↓
TRADING CALENDAR
  ↓
QUALITY ENGINE
  ↓
PIT DATASET SNAPSHOT
  ↓
PARQUET
  ↓
DUCKDB
  ↓
FEATURE / FACTOR / ALPHA / BACKTEST
```

Do not allow downstream research to bypass this path.

## 3. REQUIRED PACKAGE

Create/extend:

```text
src/quantlab/data/
```

Use clear modules, for example:

```text
sources/
raw/
catalog/
schema/
security_master/
symbols/
corporate_actions/
calendar/
quality/
pit/
snapshots/
provenance/
coverage/
survivorship/
reconciliation/
service/
repository/
cli/
```

Do not create a second data package.

## 4. SOURCE PROVENANCE

Every dataset must have immutable metadata:

```text
dataset_id
version
source
source_uri_or_reference
retrieved_at
published_at
coverage_start
coverage_end
schema_version
checksum_sha256
row_count
security_count
data_kind
license/provenance
```

Use content hashes.

Changing bytes creates a new version.

## 5. RAW DATA IMMUTABILITY

Rules:

- raw bytes copied once
- never mutate raw source
- transformations produce derived datasets
- checksum mismatch → `FAIL`
- source replacement → new version
- missing provenance → `NOT_TESTED`
- raw corruption → `FAIL`

Never silently repair raw records.

## 6. SECURITY MASTER

Create canonical:

```text
security_id
```

Tickers are labels, not identity.

Track:

- exchange
- symbol
- ISIN when supplied
- company/entity identity when supplied
- listing status
- effective intervals
- mapping provenance
- alias history
- delisting
- relisting where evidence exists

Historical symbol lookup must be as-of aware.

Example:

```text
symbol_at(security_id, T)
```

must return the historical label valid at T.

Never map a current ticker backward merely because it shares a name.

## 7. CORPORATE ACTIONS

Support explicit typed corporate actions:

- splits
- bonuses
- dividends
- rights
- mergers
- demergers
- symbol changes
- delistings
- relistings

Every action requires:

```text
announcement_time
effective_time
available_time
source
adjustment_method
```

If announcement/availability time is unknown:

```text
status = NOT_TESTED
```

Do not invent timing.

## 8. PRICE ADJUSTMENT POLICY

Separate:

```text
RAW_PRICE
ADJUSTED_PRICE
TOTAL_RETURN_PRICE
```

Never overwrite raw observations.

Adjustment must be:

- deterministic
- versioned
- explainable
- reversible where mathematically possible
- tied to corporate-action records

Research must be able to select an explicit price policy.

## 9. TRADING CALENDAR

Replace the current illustrative weekday calendar with a provider architecture capable of official sourced calendars.

Do not fabricate NSE holidays.

Represent:

```text
session_date
exchange
open_time
close_time
special_session
holiday
half_day
timezone
source
```

Calendar versions must be immutable.

A missing official calendar is `NOT_TESTED`, not assumed correct.

## 10. MARKET DATA SCHEMA

Support at least:

```text
security_id
event_time
available_time
open
high
low
close
volume
```

Optional:

```text
vwap
trade_count
bid
ask
bid_size
ask_size
```

Do not silently infer unavailable microstructure fields.

Validate:

- OHLC consistency
- non-negative volume
- timestamp ordering
- duplicate records
- impossible prices
- missing sessions
- timezone consistency
- stale observations
- split discontinuities

## 11. MULTI-SOURCE RECONCILIATION

Where multiple legitimate sources exist, compare them.

Do not automatically choose the most favorable value.

Record:

```text
source_a
source_b
difference
tolerance
resolution_policy
resolution_status
```

Unresolved discrepancy → visible data-quality issue.

## 12. SURVIVORSHIP CONTROL

Implement explicit historical universe support.

Required concept:

```text
universe.as_of(T)
```

Membership requires:

```text
effective_start
effective_end
announcement/availability provenance where relevant
```

Current constituents must never be substituted for historical membership.

Delisted securities must remain queryable historically where source data exists.

## 13. DATA QUALITY ENGINE

Create severity levels:

```text
INFO
WARN
ERROR
FAIL
NOT_TESTED
```

Quality dimensions:

- completeness
- uniqueness
- validity
- temporal consistency
- cross-source consistency
- identity consistency
- corporate-action consistency
- calendar consistency
- PIT availability
- survivorship
- adjustment integrity

Generate deterministic quality reports.

## 14. SNAPSHOTS

A research snapshot must bind:

```text
dataset versions
security master version
calendar version
corporate action version
universe version
schema version
checksums
creation metadata
```

Snapshot hash must change if any dependency changes.

Old snapshots remain immutable.

## 15. DATA LINEAGE

Every downstream experiment should be able to answer:

```text
Which raw source produced this observation?
Which transformation produced it?
Which snapshot exposed it?
Which availability timestamp made it legal?
```

Expose lineage through application APIs and Knowledge Graph nodes.

## 16. INTEGRITY FLAGS

Add or extend:

```text
future_available_data
event_available_time_conflict
source_mutation
checksum_mismatch
duplicate_observation
identity_lookahead
symbol_history_lookahead
corporate_action_lookahead
adjustment_lookahead
calendar_lookahead
universe_survivorship_leak
delisted_security_omission
cross_source_conflict
snapshot_dependency_mutation
raw_to_derived_lineage_break
timezone_mismatch
```

Direct leakage → `FAIL`.

Unknown provenance → `NOT_TESTED`.

## 17. DATA CONTRACT

Downstream engines must consume only approved interfaces.

Preferred:

```python
market_data.get(
    security_id=...,
    start=...,
    end=...,
    as_of=...
)
```

Never expose unrestricted tables to strategies.

The PIT contract remains:

```text
available_time <= as_of
```

## 18. REAL DATA IMPORT

Support controlled user-supplied/licensed files.

Example:

```text
quantlab data ingest <path>
quantlab data inspect <dataset>
quantlab data validate <dataset>
quantlab data lineage <dataset>
quantlab data snapshot <dataset>
quantlab data quality <dataset>
quantlab data reconcile <dataset-a> <dataset-b>
quantlab data security <security-id>
quantlab data corporate-actions
quantlab data calendar
quantlab data universe
```

No web scraping that bypasses provenance.

No invented data.

## 19. DESKTOP

Upgrade **Data Lab**.

Display:

- catalog
- source
- coverage
- checksums
- quality
- security master
- corporate actions
- calendar
- universe
- PIT status
- snapshot lineage

Qt remains a viewer.

No direct Parquet/DuckDB access.

## 20. TESTING

Minimum focused target: **80+ tests** covering:

- raw immutability
- checksum
- schema
- PIT
- security identity
- symbol history
- corporate actions
- adjusted prices
- calendar
- survivorship
- delisted names
- duplicates
- timezone
- source reconciliation
- snapshot hashing
- lineage
- quality statuses
- deterministic behavior
- regression across Prompts 01–19
- UI smoke

Include adversarial tests where future corporate actions, current symbol maps, current universe membership, and future rows are appended.

Historical results must remain unchanged.

## 21. PERFORMANCE

Design for:

- Parquet partition pruning
- DuckDB predicate pushdown
- vectorized validation
- incremental cataloging
- immutable snapshots
- reproducible cache keys

Do not prematurely introduce distributed infrastructure.

## 22. SAFETY

Prompt 20 must not import:

```text
kiteconnect
zerodha
openalgo
quantlab.brokers
```

It is market-data infrastructure, not order infrastructure.

## 23. NOT_TESTED

Remain explicit for:

- unavailable official NSE holiday source
- unavailable licensed history
- missing corporate-action announcement timestamps
- unavailable official index membership
- unavailable bid/ask history
- unavailable institutional data feeds

## 24. DEFINITION OF DONE

Complete only when:

- existing PIT fabric is preserved
- all raw data is immutable
- provenance/checksum works
- security identity is historical
- corporate actions are explicit
- calendar is source-backed
- survivorship controls exist
- snapshots are immutable
- data quality is deterministic
- PIT tests pass
- downstream regression passes
- documentation/ADR complete
- UI exposes data health
- no fabricated market data exists
- `LIVE_TRADING=false`

## 25. FINAL PRINCIPLE

The system must be able to say:

> **“We do not know what was knowable at T.”**

That is preferable to silently pretending the data was available.
