# QUANT LAB — CURSOR MASTER PROMPT 04
# POINT-IN-TIME DATA FABRIC
## Research-Grade Historical Data Infrastructure for Indian Markets

**Version:** 0.4  
**Date:** 2026-08-30  
**Project:** QUANT LAB  
**Purpose:** Build the foundational Point-in-Time Data Fabric without resetting or rewriting the existing system.

---

# 0. MANDATORY CONTEXT

You are continuing an existing QUANT LAB implementation.

**DO NOT RESET THE REPOSITORY.**

**DO NOT REWRITE THE EXISTING QUANTITATIVE CORE.**

**DO NOT REMOVE OR BYPASS PROMPT 01, PROMPT 02, OR PROMPT 03.**

The current system already contains:

- repository-study documentation;
- target architecture and ADRs;
- `quantlab.app`;
- `quantlab.ui`;
- provider/data abstractions;
- `MarketState`;
- strategy abstraction;
- Signal Genome / momentum slice;
- portfolio layer;
- Risk Firewall;
- OMS abstractions;
- paper broker foundation;
- next-bar backtester;
- research-integrity checks;
- experiment ledger;
- lineage;
- PySide6 desktop application;
- background-process backtest execution;
- 48+ passing tests;
- ruff/mypy-clean codebase;
- `LIVE_TRADING=false`.

The desktop application must remain a client of the application layer.

The next architectural milestone is:

> **BUILD A PROPER POINT-IN-TIME DATA FABRIC.**

This is NOT a request to merely download historical CSV files.

It is NOT a request to create a generic `data/` folder.

It is NOT a request to enlarge the synthetic dataset.

It is the foundation on which every future alpha, model, backtest, portfolio decision, AI researcher, and trading decision will depend.

---

# 1. CORE PHILOSOPHY

Treat historical financial data as a **time-indexed information system**, not merely a price table.

The fundamental research question is:

> **What information was actually available to the strategy at time T?**

Therefore:

```text
Observed Event
    +
Effective Date
    +
Availability / Publication Time
    +
Instrument Identity
    +
Corporate-Action State
    +
Dataset Version
        ↓
POINT-IN-TIME DATASET
        ↓
FEATURES / MARKETSTATE
        ↓
RESEARCH / BACKTEST
```

A backtest must never be allowed to see information that became known only after its simulated decision time.

---

# 2. POINT-IN-TIME TIMESTAMP SEMANTICS

Where applicable, distinguish:

```text
event_time
effective_time
available_time
ingested_time
```

Definitions:

### event_time
When the underlying event occurred.

### effective_time
When the event becomes economically/legal effective.

### available_time
When the information could actually have been known by the strategy.

**This is the critical timestamp for backtesting.**

### ingested_time
When QUANT LAB acquired the information.

Never conflate these timestamps.

Avoid naive datetimes in the core. Use timezone-aware timestamps.

---

# 3. ABSOLUTE ANTI-LOOK-AHEAD INVARIANT

Implement a system-level invariant:

```text
DATA.available_time <= STRATEGY.decision_time
```

If:

```text
DATA.available_time > STRATEGY.decision_time
```

the record is unavailable.

It must be excluded or produce an explicit research-integrity failure, depending on context.

Never silently leak future information.

---

# 4. REQUIRED DATA LAYERS

Implement explicit separation:

```text
data/
├── raw/
├── normalized/
├── curated/
├── pit/
├── features/
├── metadata/
└── quarantine/
```

## Raw

Immutable source artifacts.

Record:

```text
source
retrieval timestamp
original filename
checksum
schema
coverage
```

Never modify raw artifacts in place.

## Normalized

Convert provider-specific data into canonical QUANT LAB schemas.

## Curated

Validated research-ready datasets.

## Point-in-Time

Historical information states that can answer:

> What was knowable at timestamp T?

## Features

Derived variables with complete lineage to PIT inputs.

## Quarantine

Invalid or suspect records, with explicit failure reasons.

---

# 5. STORAGE ARCHITECTURE

Evaluate and implement an appropriate local analytical architecture.

Preferred direction:

```text
Parquet
+
DuckDB
```

Use transactional storage such as PostgreSQL for metadata/state where appropriate.

Conceptually:

```text
Parquet
   ↓
DuckDB
   ↓
Analytical Query
   ↓
Feature Engine
   ↓
Research
```

Transactional metadata may contain:

```text
datasets
versions
experiments
instruments
jobs
strategies
models
provenance
```

Do not force all historical market data into PostgreSQL.

Document the final architecture in an ADR.

---

# 6. CANONICAL INSTRUMENT MASTER

Create a canonical identity model.

Do NOT use ticker/symbol as the permanent identity.

Support conceptually:

```text
instrument_id
exchange
segment
symbol
trading_symbol
isin
security_type
series
currency
tick_size
lot_size
listing_date
delisting_date
status
```

Design for:

```text
NSE
BSE
future exchanges/markets
```

without provider-specific leakage into strategy code.

---

# 7. INSTRUMENT IDENTITY AND SYMBOL CHANGES

Historical symbol changes must not destroy identity continuity.

Support:

```text
instrument_id
    ↓
historical symbol(s)
    ↓
current symbol
```

Do not assume:

```text
same symbol = same security
```

or:

```text
different symbol = different security
```

Use authoritative identifiers wherever possible.

---

# 8. TRADING CALENDAR

Create a market-calendar abstraction supporting:

```text
exchange
segment
trading date
session open
session close
special sessions
holidays
early close
expiry dates
```

The backtester must not invent trading sessions.

Do not forward-fill across non-trading sessions unless explicitly defined by the feature.

---

# 9. CANONICAL OHLCV SCHEMA

At minimum:

```text
instrument_id
timestamp
open
high
low
close
volume
```

Prefer:

```text
exchange
timeframe
currency
source_id
dataset_version
```

Validate:

```text
high >= max(open, close)
low <= min(open, close)
high >= low
volume >= 0
```

Invalid records must not enter curated research storage.

---

# 10. BAR TIMESTAMP CONTRACT

Document:

```text
timezone
session date
bar start/end convention
timestamp precision
```

Where appropriate distinguish:

```text
bar_open_time
bar_close_time
```

Never leave the meaning of a timestamp implicit.

---

# 11. CORPORATE-ACTION MODEL

Create a canonical model supporting architecture for:

```text
dividend
split
bonus
rights
merger
demerger
spin-off
symbol change
face-value change
```

Support fields such as:

```text
action_id
instrument_id
event_type
announcement_time
record_date
ex_date
effective_date
payment_date
ratio/value
source
```

If the source does not provide an authoritative timestamp, do not invent one. Mark it unavailable.

---

# 12. ADJUSTED VS UNADJUSTED DATA

Never mix these silently.

Support explicit representations:

```text
RAW_PRICE
ADJUSTED_PRICE
TOTAL_RETURN_SERIES
```

Every experiment must record:

```text
price_adjustment_method
corporate_action_policy
```

A researcher must know exactly what price representation was used.

---

# 13. DIVIDEND POLICY

Do not automatically embed dividends into prices.

Support explicit research policies such as:

```text
price_return
total_return
cash_dividend
```

Document the chosen treatment.

---

# 14. SURVIVORSHIP BIAS

The historical universe must be reconstructable.

Support:

```text
listing_date
delisting_date
status_history
index_membership_history
```

Never define historical universes solely using today's active securities.

---

# 15. POINT-IN-TIME UNIVERSE

Implement an API conceptually equivalent to:

```python
universe.as_of(timestamp)
```

It must return only securities valid for that historical timestamp according to the configured universe definition.

The system must eventually support questions such as:

```text
Which securities belonged to NIFTY on 2018-01-01?
Which securities belonged to NIFTY on 2022-01-01?
Which securities belonged to NIFTY on 2026-01-01?
```

Do not use today's constituent list for historical simulation.

---

# 16. FUNDAMENTAL DATA MODEL

Design the architecture now even if ingestion is initially limited.

Fundamental observations should support:

```text
metric
value
period_start
period_end
publication_time
available_time
source
revision
```

Examples:

```text
revenue
EBITDA
EPS
debt
cash
ROE
ROIC
```

Critical invariant:

```text
period_end != available_time
```

A Q1 result is not necessarily known on the last day of Q1.

---

# 17. FUNDAMENTAL REVISIONS

Do not overwrite historical observations blindly.

Example:

```text
Observation A
available_time = T1

Revision B
available_time = T2
```

A backtest at T1 must see A.

A backtest at T2 may see B.

Preserve the revision history.

---

# 18. DATA VERSIONING

Every dataset must have an explicit version.

Example:

```text
NSE_EQUITY_DAILY_v1
NSE_EQUITY_DAILY_v1.1
```

A version should identify:

```text
schema
source
transformation
adjustment policy
coverage
creation time
checksum
```

Never silently mutate a dataset already used by an experiment.

---

# 19. DATA SNAPSHOTS

Experiments must be reproducible.

Each experiment must reference:

```text
dataset_version
snapshot_id
```

A later update to the data must not silently change the meaning of an old experiment.

---

# 20. PROVENANCE AND LINEAGE

Every dataset and derived object must maintain lineage.

Required conceptual chain:

```text
Source
 ↓
Raw Artifact
 ↓
Normalization
 ↓
Validation
 ↓
Corporate-Action Transformation
 ↓
PIT Transformation
 ↓
Feature
 ↓
Signal
 ↓
Strategy
 ↓
Experiment
```

Extend the existing experiment ledger and lineage system rather than creating a competing system.

---

# 21. CHECKSUMS

Calculate checksums such as:

```text
SHA-256
```

for immutable source artifacts.

Store:

```text
artifact_hash
```

This permits detection of accidental or unauthorized mutation.

---

# 22. DATA QUALITY ENGINE

Implement deterministic validation.

## Structural

```text
schema
required fields
data types
timezone
```

## Temporal

```text
duplicate timestamps
out-of-order records
future timestamps
missing sessions
unexpected gaps
```

## OHLC

```text
high/low consistency
negative prices
zero/negative volume
```

## Instrument

```text
unknown instrument
duplicate identity
invalid listing interval
```

## Corporate Actions

```text
invalid dates
inconsistent ratios
missing adjustment information
```

---

# 23. DATASET STATES

Each dataset should have explicit state:

```text
RAW
INGESTED
NORMALIZED
VALIDATED
CURATED
PIT_VALIDATED
RESEARCH_READY
QUARANTINED
DEPRECATED
```

A file existing on disk does NOT imply research readiness.

---

# 24. RESEARCH-INTEGRITY INTEGRATION

Integrate the Data Fabric with the existing Research Integrity Engine.

Extend it with checks for:

```text
PIT availability
dataset version
universe history
corporate-action policy
adjustment policy
timestamp semantics
data leakage
```

Use:

```text
PASS
WARN
FAIL
NOT_TESTED
```

Never convert:

```text
NOT_TESTED → PASS
```

---

# 25. BACKTESTER INTEGRATION

The backtester must obtain research data through the Data Fabric.

Prohibited:

```python
pandas.read_csv("arbitrary_future_data.csv")
```

Preferred:

```text
Backtest
 ↓
Data Fabric Query
 ↓
PIT Filter
 ↓
Universe Filter
 ↓
Feature Calculation
 ↓
Strategy
```

The existing next-bar fill rule remains intact.

---

# 26. PIT QUERY CONTRACT

Create a canonical query abstraction conceptually equivalent to:

```python
dataset.query(
    instruments=...,
    start=...,
    end=...,
    as_of=decision_time,
)
```

The exact implementation is your engineering decision.

The invariant is:

> The returned information must be limited to information available at the requested as-of time.

---

# 27. AS-OF TESTS

Mandatory automated tests:

```text
future record exists
        ↓
as-of query
        ↓
future record excluded
```

and:

```text
revision arrives at T2
        ↓
query as of T1
        ↓
revision excluded
```

Also test:

```text
historical universe reconstruction
```

and:

```text
corporate-action information availability
```

where supported.

---

# 28. FEATURE ENGINEERING

Features must inherit data lineage.

A feature should identify:

```text
feature_id
feature_name
calculation_version
input_dataset
input_columns
window
availability_time
creation_time
```

For example:

```text
momentum_20
```

must demonstrably use only permitted historical information.

---

# 29. FEATURE LOOKBACK

Define lookback semantics explicitly.

For example:

```text
momentum_20 = 20 trading observations
```

unless a different convention is explicitly configured.

Do not silently interpret trading-day windows as calendar-day windows.

---

# 30. FEATURE WARM-UP

Explicitly handle insufficient history.

Possible states:

```text
READY
INSUFFICIENT_HISTORY
MISSING_DATA
INVALID
```

Never fill missing history using future information.

---

# 31. PROVIDER ABSTRACTION

Keep provider-specific code isolated.

Conceptually:

```text
DataProvider
├── SyntheticProvider
├── LocalParquetProvider
├── NSEProvider
├── BSEProvider
└── FutureProvider
```

Providers must return canonical QUANT LAB objects.

Strategies must never import provider-specific APIs.

---

# 32. REAL INDIAN-MARKET DATA

Target:

```text
NSE
BSE
Indian equities
Indian market calendar
corporate actions
historical index membership
```

Do not hardcode one vendor's schema into the domain model.

---

# 33. FIRST REAL INGESTION

When a legitimate historical source is available:

1. Identify and document the source.
2. Preserve the raw artifact.
3. Calculate checksum.
4. Normalize into canonical schema.
5. Validate.
6. Map instruments.
7. Build calendar information.
8. Apply explicit corporate-action policy.
9. Build PIT representation where the source supports it.
10. Run integrity checks.
11. Mark research readiness only when justified.

If the source lacks information required to prove PIT correctness:

```text
NOT_TESTED
```

or:

```text
WARN
```

Do not fabricate correctness.

---

# 34. ABSOLUTE NO-FABRICATION RULE

Prohibited:

```text
✗ synthetic data presented as real
✗ invented corporate actions
✗ invented publication timestamps
✗ guessed adjustment factors
✗ fabricated historical constituents
✗ fabricated provider provenance
```

Synthetic data remains allowed for deterministic tests and architecture diagnostics.

It must be labeled:

```text
SYNTHETIC
```

---

# 35. SYNTHETIC/REAL SEPARATION

Keep the current synthetic vertical slice working.

The synthetic provider and real provider must use the same canonical interfaces.

This allows:

```text
synthetic tests
```

without contaminating:

```text
real research
```

---

# 36. DATA CATALOG

Create a local data catalog that can answer:

```text
What datasets exist?
Where are they stored?
What period do they cover?
Which instruments?
Which provider?
Which version?
What validation status?
What PIT guarantees?
```

Conceptual fields:

```text
dataset_id
version
source
coverage
schema
storage
checksum
validation_status
PIT_status
created_at
```

---

# 37. DATASET REGISTRY

Build a programmatic registry.

The research engine must reference:

```text
dataset_id
```

rather than hardcoded filesystem paths.

---

# 38. INGESTION JOBS

Use the existing application job infrastructure.

A typical ingestion job:

```text
QUEUED
 ↓
DOWNLOADING
 ↓
RAW_STORED
 ↓
NORMALIZING
 ↓
VALIDATING
 ↓
CURATING
 ↓
PIT_BUILD
 ↓
COMPLETED
```

Failures must preserve diagnostic information.

---

# 39. IDEMPOTENCY

Repeated ingestion of identical source content must not corrupt the dataset.

Use combinations of:

```text
source identity
checksum
dataset version
```

to detect duplicates.

---

# 40. INCREMENTAL INGESTION

Design for future incremental updates:

```text
existing history
+
new observations
```

Correctness has priority over ingestion speed.

---

# 41. DATA RETENTION

Do not automatically delete historical datasets.

Support explicit states:

```text
ACTIVE
ARCHIVED
DEPRECATED
QUARANTINED
```

Research data may be evidence for old experiments.

---

# 42. EXPERIMENT REPRODUCIBILITY

Every backtest experiment must record:

```text
dataset_id
dataset_version
snapshot_id
instrument universe
calendar
adjustment policy
PIT policy
feature versions
strategy version
parameters
cost model
slippage model
software version
```

This is mandatory.

---

# 43. EXPERIMENT LEDGER

Extend the existing JSONL ledger rather than replacing it.

Conceptually:

```json
{
  "experiment_id": "...",
  "dataset_id": "...",
  "dataset_version": "...",
  "snapshot_id": "...",
  "pit_policy": "...",
  "adjustment_policy": "...",
  "universe_version": "...",
  "feature_versions": [],
  "strategy_version": "...",
  "research_integrity": {}
}
```

---

# 44. LINEAGE

The lineage graph should eventually support:

```text
Dataset
   ↓
Snapshot
   ↓
PIT Query
   ↓
Feature
   ↓
Signal
   ↓
Portfolio
   ↓
Backtest
   ↓
Experiment
```

Every result should be traceable to its source data.

---

# 45. DATA CONTRACTS

Create typed schemas/contracts for:

```text
Instrument
Bar
CorporateAction
FundamentalObservation
MarketSession
Dataset
DatasetSnapshot
DataQualityReport
PITRecord
Feature
```

Use immutable models where appropriate.

Maintain:

```text
mypy --strict
```

Do not sacrifice type safety for implementation speed.

---

# 46. TESTING REQUIREMENTS

Add tests for:

### Instruments

```text
identity
listing
delisting
symbol changes
```

### Bars

```text
OHLC validation
duplicates
timezone
missing sessions
```

### PIT

```text
as-of filtering
future exclusion
revision handling
```

### Corporate Actions

```text
event dates
adjustment policy
```

### Universe

```text
historical membership
survivorship protection
```

### Provenance

```text
checksum
dataset version
lineage
```

### Backtester

```text
cannot bypass PIT provider
```

---

# 47. PROPERTY-BASED TESTING

Where useful, add property-based tests.

Important properties:

```text
No PIT query returns available_time > as_of.
```

```text
No invalid OHLC record reaches curated storage.
```

```text
A dataset snapshot remains reproducible.
```

These properties are more valuable than superficial test counts.

---

# 48. FAILURE MODES

Explicitly handle:

```text
provider unavailable
corrupt source
schema change
missing field
duplicate data
partial download
checksum mismatch
invalid timestamp
unknown instrument
missing PIT metadata
```

Do not silently continue if research validity is compromised.

---

# 49. FAILURE-CLOSED RESEARCH

If a dataset cannot establish the required integrity:

```text
DO NOT RUN AS RESEARCH-GRADE
```

Use:

```text
NOT_READY
```

or:

```text
FAIL
```

This is mandatory.

---

# 50. PERFORMANCE

Design for large historical datasets.

Prefer:

```text
columnar storage
partitioning
predicate pushdown
DuckDB
streaming/chunked ingestion
```

Avoid loading an entire market history into RAM unnecessarily.

Correctness comes before premature optimization.

---

# 51. PARTITIONING

Evaluate partition strategies such as:

```text
exchange/
year/
instrument/
date/
```

Choose based on actual research query patterns.

Avoid creating thousands of tiny files unnecessarily.

Document the decision.

---

# 52. OBSERVABILITY

Log:

```text
dataset_id
job_id
snapshot_id
provider
record counts
validation counts
quarantine counts
duration
```

Track:

```text
rows ingested
rows accepted
rows rejected
duplicate count
missing count
invalid count
coverage
instrument count
```

---

# 53. CLI

Extend the existing CLI using its current conventions.

Conceptual commands:

```text
quantlab data list
quantlab data inspect <dataset>
quantlab data validate <dataset>
quantlab data ingest <source>
quantlab data status
quantlab data pit-check <dataset>
```

Do not create a second CLI architecture.

---

# 54. DESKTOP INTEGRATION

After the data service works, expose a modest Data area:

```text
Data
 ├── Catalog
 ├── Health
 ├── Coverage
 └── PIT Status
```

Do not move ingestion or PIT logic into Qt.

Correct boundary:

```text
Qt UI
 ↓
Application Service
 ↓
Data Fabric
```

---

# 55. AI BOUNDARY

AI must never bypass the Data Fabric.

Prohibited:

```text
AI agent
 ↓
arbitrary download
 ↓
direct backtest
```

Required future architecture:

```text
AI request
 ↓
Data Fabric
 ↓
validated dataset
 ↓
Research Engine
```

---

# 56. BROKER BOUNDARY

The Data Fabric remains independent of live execution.

Do not mix:

```text
historical ingestion
```

with:

```text
broker order execution
```

They are separate bounded contexts.

---

# 57. NO LIVE TRADING IN THIS TASK

Do NOT implement:

```text
Zerodha live orders
OpenAlgo live orders
autonomous execution
```

Live trading remains:

```text
FALSE
```

---

# 58. NO AUTONOMOUS AI IN THIS TASK

Do NOT implement autonomous strategy generation or trading here.

Prepare clean interfaces for future AI research.

---

# 59. DOCUMENTATION

Create/update:

```text
docs/architecture/QUANT_LAB_DATA_FABRIC.md
docs/architecture/PIT_DATA_ARCHITECTURE.md
docs/architecture/DATA_STORAGE_ARCHITECTURE.md
docs/architecture/DATA_PROVENANCE.md
docs/architecture/DATA_QUALITY.md
```

Create ADRs for major decisions after inspecting existing ADR numbering:

```text
Parquet/DuckDB analytical storage
canonical instrument identity
PIT timestamp semantics
dataset versioning
corporate-action policy
```

Do not duplicate existing ADRs.

---

# 60. INSPECT BEFORE CODING

Before changing code, inspect:

```text
src/quantlab/data
MarketState
provider abstractions
backtester
research integrity
experiment ledger
lineage
application job system
existing docs
ADR numbering
tests
Makefile
CLI
```

Then reconcile the Data Fabric with the existing architecture.

Do not blindly create parallel systems.

---

# 61. MIGRATION PRINCIPLE

If an existing abstraction is insufficient:

```text
extend it
```

rather than:

```text
delete it and replace everything
```

Existing synthetic tests must continue passing.

---

# 62. FIRST IMPLEMENTATION VERTICAL SLICE

Build:

```text
Source
 ↓
Raw artifact
 ↓
Checksum
 ↓
Normalization
 ↓
Validation
 ↓
Parquet
 ↓
DuckDB
 ↓
PIT query
 ↓
MarketState
 ↓
existing momentum strategy
 ↓
existing backtester
 ↓
existing integrity engine
 ↓
existing experiment ledger
```

Keep the synthetic provider operational.

---

# 63. FIRST REAL DATASET

After the infrastructure works, ingest one carefully selected legitimate real Indian-market dataset.

Prioritize:

```text
quality
provenance
schema clarity
historical coverage
timestamp integrity
```

over the number of securities.

A smaller trustworthy dataset is more valuable than a massive contaminated dataset.

---

# 64. DATASET RESEARCH GATE

Before allowing real data into research:

```text
DATASET RESEARCH GATE
---------------------
Source known?             PASS/FAIL
Checksum recorded?        PASS/FAIL
Schema validated?         PASS/FAIL
Timezone defined?         PASS/FAIL
Trading calendar valid?   PASS/FAIL
Instrument identity?      PASS/FAIL
OHLC valid?               PASS/FAIL
Corporate actions?        PASS/WARN/NOT_TESTED
PIT verified?             PASS/WARN/FAIL
Survivorship verified?    PASS/WARN/FAIL
Provenance complete?      PASS/FAIL
```

Do not hide uncertainty.

---

# 65. DEFINITION OF DONE

This Prompt 04 is complete only when:

```text
✓ Existing Prompt 01/02/03 architecture remains intact.
✓ Existing synthetic slice still runs.
✓ Existing tests still pass.
✓ Parquet/DuckDB architecture is implemented or explicitly justified.
✓ Canonical instrument model exists.
✓ Canonical bar model exists.
✓ Trading calendar abstraction exists.
✓ Corporate-action abstraction exists.
✓ Dataset registry exists.
✓ Dataset versioning exists.
✓ Raw/normalized/curated/PIT layers exist.
✓ Provenance exists.
✓ Checksums exist.
✓ Data quality engine exists.
✓ Quarantine exists.
✓ PIT query contract exists.
✓ As-of filtering is tested.
✓ Future-data exclusion is tested.
✓ Historical-universe architecture exists.
✓ Backtester consumes the Data Fabric rather than arbitrary files.
✓ Experiment ledger records dataset provenance.
✓ Lineage connects dataset → feature → strategy → experiment.
✓ Real-data ingestion path exists.
✓ One legitimate real Indian-market dataset can be ingested when available.
✓ Research readiness is explicitly gated.
✓ NOT_TESTED remains NOT_TESTED.
✓ Desktop remains responsive.
✓ No live trading is enabled.
✓ ruff remains clean.
✓ mypy --strict remains clean.
✓ Tests are expanded meaningfully.
✓ Documentation and ADRs are updated.
```

---

# 66. CRITICAL RESEARCH INVARIANTS

These are non-negotiable.

### Invariant 1
A strategy cannot access future information.

### Invariant 2
Every backtest knows exactly which dataset version and snapshot it used.

### Invariant 3
A dataset cannot become research-ready without passing required integrity gates.

### Invariant 4
Historical universes cannot silently use today's constituents.

### Invariant 5
Corporate-action adjustments are explicit.

### Invariant 6
Fundamental revisions preserve availability history.

### Invariant 7
Synthetic data is never confused with real market data.

### Invariant 8
`NOT_TESTED` is never `PASS`.

### Invariant 9
The UI cannot bypass the Data Fabric.

### Invariant 10
AI cannot bypass the Data Fabric.

### Invariant 11
Live trading remains disabled.

---

# 67. SCIENTIFIC STANDARD

Treat the Data Fabric as the measurement instrument of a quantitative laboratory.

If the measurement instrument is wrong:

```text
beautiful mathematics
+
excellent ML
+
powerful AI
=
invalid conclusion
```

Therefore:

> **Data correctness has priority over model sophistication.**

Do not optimize for:

```text
impressive dashboards
high backtest Sharpe
large synthetic returns
```

Optimize for:

```text
truth
reproducibility
temporal correctness
provenance
falsifiability
```

---

# 68. FINAL CURSOR DIRECTIVE

**CONTINUE FROM THE CURRENT QUANT LAB WORKSPACE.**

**DO NOT RESET ANYTHING.**

**DO NOT REWRITE THE QUANTITATIVE ENGINE.**

**DO NOT REMOVE PROMPT 01, PROMPT 02, OR PROMPT 03 WORK.**

First inspect the actual current repository.

Then implement the Point-in-Time Data Fabric as a proper foundational subsystem.

The implementation must be:

```text
local-first
typed
testable
versioned
provenance-aware
PIT-correct
research-integrity-aware
Indian-market-ready
provider-agnostic
desktop-compatible
```

The objective is NOT:

> "Get some NSE CSV files into Python."

The objective is:

> **Build a research-grade historical information system capable of reconstructing what QUANT LAB could legitimately have known at any historical decision time.**

Everything that eventually becomes an alpha, model, portfolio, AI hypothesis, or trading decision will depend on this.

Build the foundation accordingly.

Proceed autonomously through:

```text
inspection
→ architecture reconciliation
→ implementation
→ migration
→ tests
→ validation
→ documentation
→ CLI integration
→ application integration
```

Stop only when the Definition of Done and Critical Research Invariants are satisfied, or explicitly report the exact blocker instead of fabricating completion.
