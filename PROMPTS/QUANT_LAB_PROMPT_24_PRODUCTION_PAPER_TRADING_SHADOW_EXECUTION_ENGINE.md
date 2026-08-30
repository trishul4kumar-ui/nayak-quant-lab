# QUANT LAB — PROMPT 24
# Production Paper Trading & Shadow Execution Engine

**Target Version:** `2.4.0`  
**Prompt:** `24`  
**Status:** Engineering Specification / Implementation Prompt  
**Classification:** Production Research Infrastructure — NO LIVE ORDER ROUTING

---

## 0. EXECUTION DIRECTIVE

Implement **Prompt 24 — Production Paper Trading & Shadow Execution Engine** on the **existing QUANT LAB 2.3.x architecture**.

This prompt must **extend and compose the existing system**. It must NOT rewrite, fork, duplicate, or replace any previous engine.

The objective is to create an institutional-grade **production paper-trading and shadow-execution environment** capable of running the complete QUANT LAB decision pipeline against **live/current market data**, while maintaining a hard architectural boundary that makes actual broker order submission impossible.

### PRIMARY QUESTION

> **“If QUANT LAB were operating in production right now, what would it decide, what orders would it intend to generate, what would those orders hypothetically experience in the market, and how would the resulting portfolio evolve — without sending a single order to a broker?”**

The system must therefore model the complete production decision loop:

```text
LIVE MARKET DATA
      ↓
PIT / AVAILABILITY VALIDATION
      ↓
MARKET STATE
      ↓
FEATURES
      ↓
ALPHA / FACTORS / REGIMES
      ↓
MODELS / ADAPTIVE LEARNERS / ENSEMBLES
      ↓
RESEARCH GATE
      ↓
CAPITAL ALLOCATION
      ↓
TARGET PORTFOLIO
      ↓
PAPER OMS
      ↓
SHADOW ORDER INTENT
      ↓
SHADOW EXECUTION
      ↓
PAPER FILLS
      ↓
PAPER ACCOUNT / POSITIONS
      ↓
MONITORING / ATTRIBUTION / TCA
      ↓
RECONCILIATION
      ↓
KNOWLEDGE / LEDGER / AUDIT
```

### ABSOLUTE SAFETY PROPERTY

```text
LIVE_TRADING = FALSE
```

This property is mandatory.

No AI, model, strategy, UI action, configuration, environment variable, experiment, shadow order, or software component introduced by Prompt 24 may cause a real broker order to be submitted.

---

# 1. NON-NEGOTIABLE ARCHITECTURAL PRINCIPLES

The implementation must preserve the following separation:

```text
DATA
≠
MARKET STATE
≠
FEATURE
≠
FACTOR
≠
ALPHA
≠
REGIME
≠
MODEL
≠
ADAPTIVE LEARNER
≠
ENSEMBLE
≠
PORTFOLIO
≠
CAPITAL DECISION
≠
ORDER INTENT
≠
PAPER ORDER
≠
SHADOW ORDER
≠
PAPER FILL
≠
POSITION
≠
BROKER ORDER
≠
BROKER CONFIRMATION
```

Prompt 24 must never collapse these abstractions.

### Critical distinction

```text
SHADOW EXECUTION ≠ PAPER OMS ≠ BROKER EXECUTION
```

Prompt 18 already owns the paper OMS.

Prompt 13 already owns execution-research models.

Prompt 21 owns institutional TCA and capacity calibration.

Prompt 23 owns model-risk / independent validation / certification governance.

Prompt 24 composes those systems into a **continuous production-like paper/shadow operating environment**.

It does not create competing implementations.

---

# 2. SCOPE

Prompt 24 shall provide:

1. Live/current market-data ingestion into the existing data fabric.
2. Production-like market-data scheduling.
3. Decision-cycle orchestration.
4. Shadow portfolio state.
5. Shadow order generation.
6. Paper execution simulation.
7. Real-time / near-real-time paper accounting.
8. Position and cash reconciliation.
9. Execution-latency measurement.
10. Shadow-vs-paper comparison.
11. Decision snapshots.
12. Full lineage.
13. Operational event logging.
14. Failure handling.
15. Restart/recovery.
16. Duplicate-cycle protection.
17. Data-staleness protection.
18. Market-session awareness.
19. Kill-switch behavior.
20. Monitoring integration.
21. TCA integration.
22. Knowledge-graph integration.
23. Certification-state enforcement.
24. Production-readiness diagnostics.

It must NOT provide:

- Live broker order placement.
- Live order modification.
- Live order cancellation.
- Live broker authentication for trading.
- Automatic live promotion.
- Autonomous capital expansion.
- AI-controlled live trading.
- A second backtester.
- A second paper OMS.
- A second data fabric.
- A second risk engine.
- A second TCA engine.

---

# 3. ARCHITECTURAL POSITION

Prompt 24 sits after Prompt 23 governance and around Prompt 18 paper execution:

```text
PROMPTS 01–16
RESEARCH FOUNDATION
        ↓
PROMPT 17
CAPITAL ALLOCATION
        ↓
PROMPT 18
PAPER OMS
        ↓
PROMPTS 19–21
MONITORING / DATA / TCA
        ↓
PROMPT 22
ECONOMETRICS
        ↓
PROMPT 23
VALIDATION & CERTIFICATION
        ↓
────────────────────────────────────
PROMPT 24
PRODUCTION PAPER / SHADOW ENGINE
────────────────────────────────────
        ↓
PAPER / SHADOW ONLY
        ↓
NO LIVE BROKER ROUTING
```

Prompt 24 must establish the operational bridge toward future broker integration without actually creating the live trading path.

---

# 4. NEW PACKAGE

Create:

```text
src/quantlab/shadow/
```

Recommended modules:

```text
shadow/
├── __init__.py
├── models.py
├── enums.py
├── errors.py
├── config.py
├── session.py
├── scheduler.py
├── cycle.py
├── decision.py
├── snapshot.py
├── market.py
├── state.py
├── portfolio.py
├── order_intent.py
├── shadow_order.py
├── execution.py
├── fills.py
├── accounting.py
├── reconciliation.py
├── latency.py
├── slippage.py
├── synchronization.py
├── idempotency.py
├── checkpoint.py
├── recovery.py
├── health.py
├── safety.py
├── audit.py
├── lineage.py
├── repository.py
├── service.py
├── reporting.py
├── experiment.py
├── cli.py
└── library.py
```

Keep:

```python
quantlab.shadow.__init__
```

thin.

Do not introduce circular imports.

---

# 5. SHADOW OPERATING MODES

Implement explicit operating modes.

```text
OFF
RESEARCH_PAPER
PAPER
SHADOW
PAUSED
HALTED
ERROR
RECOVERY
```

Recommended semantics:

### OFF

No cycle execution.

### RESEARCH_PAPER

Production-like pipeline using research/synthetic data.

### PAPER

Uses production/current market data and paper account state.

### SHADOW

Produces decisions and hypothetical execution records against current market conditions.

### PAUSED

No new decisions or orders.

### HALTED

Safety state. New exposure prohibited.

### ERROR

Critical execution or data failure.

### RECOVERY

State restoration and reconciliation before resuming.

Never silently transition between modes.

---

# 6. SHADOW CYCLE

Every production cycle must be immutable and identifiable.

Create:

```text
ShadowCycle
```

with:

```text
cycle_id
run_id
decision_time
market_time
data_snapshot_id
data_snapshot_hash
strategy_version
feature_snapshot_hash
model_snapshot_hash
ensemble_snapshot_hash
regime_snapshot_hash
risk_snapshot_hash
capital_decision_hash
target_portfolio_hash
order_plan_hash
execution_policy_hash
configuration_hash
mode
status
created_at
completed_at
```

A cycle must be reproducible from its recorded snapshot identities.

---

# 7. PRODUCTION DECISION LOOP

Implement:

```text
WAIT
 ↓
CHECK SESSION
 ↓
CHECK DATA HEALTH
 ↓
CHECK DATA FRESHNESS
 ↓
FREEZE SNAPSHOT
 ↓
COMPUTE MARKET STATE
 ↓
COMPUTE FEATURES
 ↓
COMPUTE ALPHA
 ↓
COMPUTE MODELS
 ↓
COMPUTE ENSEMBLES
 ↓
COMPUTE REGIME
 ↓
RUN RESEARCH / SAFETY GATES
 ↓
CAPITAL ALLOCATION
 ↓
TARGET PORTFOLIO
 ↓
PAPER OMS
 ↓
SHADOW EXECUTION
 ↓
ACCOUNTING
 ↓
RECONCILIATION
 ↓
MONITORING
 ↓
TCA
 ↓
KNOWLEDGE / LEDGER
 ↓
CHECKPOINT
```

Each stage must have explicit success/failure state.

No silent continuation after a critical failure.

---

# 8. DATA FRESHNESS

Production paper trading requires strict freshness checks.

Implement:

```text
data_timestamp
received_timestamp
available_time
decision_time
processing_time
latency_ms
age_ms
```

Define configurable thresholds:

```text
MAX_DATA_AGE
MAX_CLOCK_SKEW
MAX_PROCESSING_LATENCY
MAX_MISSING_INTERVAL
```

If data is stale:

```text
STALE_DATA
```

must be emitted.

Depending on policy:

```text
ABSTAIN
PAUSE
HALT
```

No stale data may silently generate a trade decision.

---

# 9. POINT-IN-TIME REQUIREMENT

The existing Prompt 04 fabric remains authoritative.

Every decision must satisfy:

```text
available_time <= decision_time
```

The engine must reject:

```text
available_time > decision_time
```

as future information.

Prompt 24 must never use a later quote to improve an earlier simulated decision.

---

# 10. MARKET SESSION ENGINE

Integrate Prompt 20's production calendar.

Do not create a new calendar engine.

Session states:

```text
PRE_OPEN
OPEN
CONTINUOUS
AUCTION
CLOSE
POST_CLOSE
HOLIDAY
HALT
UNKNOWN
```

Unknown calendar state must never be interpreted as OPEN.

If the official calendar is unavailable:

```text
calendar_status = NOT_TESTED
```

or:

```text
ABSTAIN
```

according to policy.

Never invent NSE/BSE holidays.

---

# 11. DECISION CLOCK

Implement explicit clock semantics.

A decision may be triggered by:

```text
BAR_CLOSE
SCHEDULED_INTERVAL
EVENT
MANUAL_PAPER_RUN
RECOVERY_REPLAY
```

Each trigger must have:

```text
trigger_id
trigger_time
source
decision_time
```

Duplicate triggers for the same decision timestamp must be idempotent.

---

# 12. SNAPSHOT FREEZE

At the beginning of every decision cycle:

```text
FREEZE
```

the exact inputs.

Snapshot must contain:

```text
market data
features
labels if applicable
factor state
regime state
model state
adaptive state
ensemble state
risk state
capital policy
portfolio state
execution policy
configuration
```

No component may mutate the snapshot after freeze.

---

# 13. PRODUCTION PAPER ACCOUNT

Prompt 18 remains authoritative for paper accounting.

Prompt 24 must use:

```text
PaperAccount
```

with:

```text
account_id
cash
reserved_cash
investable_cash
positions
equity
realized_pnl
unrealized_pnl
fees
turnover
drawdown
```

Maintain:

```text
equity = cash + market_value + other_accounted_assets
```

Cash and position accounting must reconcile exactly within explicitly configured numerical tolerance.

---

# 14. SHADOW PORTFOLIO

Maintain a separate:

```text
ShadowPortfolio
```

representing:

> What the system believes it would hold if the shadow decisions were executed.

It must not be confused with the actual brokerage account.

Explicitly label:

```text
SHADOW_POSITION
PAPER_POSITION
BROKER_POSITION
```

as separate states.

---

# 15. ORDER INTENT

Reuse Prompt 18 order-intent semantics.

Order intent must derive from:

```text
Δq = target_qty - current_qty
```

Never infer a BUY simply because target weight is positive.

Order intent contains:

```text
intent_id
cycle_id
symbol
security_id
side
target_qty
current_qty
delta_qty
limit/reference_price
notional
reason
decision_hash
target_hash
timestamp
```

---

# 16. SHADOW ORDER

Create:

```text
ShadowOrder
```

distinct from:

```text
PaperOrder
```

A shadow order is a production-like hypothetical order instruction.

It must never be routable to a broker.

Required:

```text
shadow_order_id
intent_id
cycle_id
security_id
side
quantity
reference_price
arrival_time
expected_fill_model
execution_policy
status
```

---

# 17. EXECUTION SIMULATION

Reuse Prompt 13 execution models and Prompt 18 paper execution.

Do not create a second slippage/impact implementation.

Execution may model:

```text
spread
slippage
market impact
latency
partial fills
liquidity
participation
fees
residual quantity
```

Every simulated fill must record:

```text
reference_price
execution_price
spread_cost
slippage_cost
impact_cost
commission
other_cost
gross_notional
net_notional
filled_quantity
residual_quantity
```

---

# 18. REAL-TIME SHADOW EXECUTION

The system should support:

```text
decision
→ timestamp
→ order arrival
→ simulated fill opportunity
→ simulated fill
→ residual
```

Latency must be measured:

```text
market → decision
decision → intent
intent → shadow order
shadow order → simulated fill
total cycle latency
```

Never use future market information to calculate a historical fill.

---

# 19. PARTIAL FILLS

Never assume:

```text
100% fill
```

unless the execution policy explicitly permits it and the model can justify it.

Unknown volume:

```text
NOT_TESTED
```

not infinite liquidity.

Residual quantity must remain visible.

---

# 20. PAPER VS SHADOW

Support both:

### PAPER

A simulated account whose orders are processed by the paper OMS.

### SHADOW

A hypothetical production decision/execution stream that does not necessarily alter the canonical paper account.

Provide comparison:

```text
shadow_target
paper_target
shadow_order
paper_order
shadow_fill
paper_fill
shadow_position
paper_position
```

Differences must be explainable.

---

# 21. RECONCILIATION

Implement continuous reconciliation between:

```text
decision
→ target
→ intent
→ order
→ fill
→ position
→ cash
→ equity
```

Any unexplained difference becomes:

```text
RECONCILIATION_BREAK
```

Never auto-repair silently.

Required reconciliation hash:

```text
reconciliation_hash
```

---

# 22. STATE MACHINE

Implement a strict state machine.

Example:

```text
CREATED
 ↓
VALIDATED
 ↓
PLANNED
 ↓
SUBMITTED_PAPER
 ↓
PARTIALLY_FILLED
 ↓
FILLED
 ↓
RECONCILED
 ↓
CLOSED
```

Shadow lifecycle may use:

```text
CREATED
VALIDATED
SIMULATED
PARTIAL
COMPLETED
RECONCILED
ABSTAINED
REJECTED
```

Illegal transitions must raise:

```text
InvalidShadowTransition
```

---

# 23. IDEMPOTENCY

Repeated execution of the same cycle must not create duplicate state.

Idempotency key:

```text
strategy_version
+
decision_time
+
data_snapshot_hash
+
portfolio_state_hash
+
configuration_hash
```

Same key:

```text
same result
```

not:

```text
duplicate order
```

---

# 24. RESTART / RECOVERY

Production systems must survive process crashes.

Implement checkpoints:

```text
cycle checkpoint
portfolio checkpoint
paper account checkpoint
shadow state checkpoint
last processed market timestamp
```

On restart:

```text
LOAD CHECKPOINT
 ↓
VERIFY HASH
 ↓
RECONCILE
 ↓
CHECK DATA FRESHNESS
 ↓
RESUME OR ABSTAIN
```

Corrupt checkpoints must cause a safe failure.

---

# 25. KILL SWITCH

Implement multiple independent kill conditions.

Examples:

```text
manual_halt
data_stale
calendar_unknown
reconciliation_break
paper_accounting_break
model_integrity_fail
risk_limit_breach
capital_decision_invalid
execution_integrity_fail
configuration_mismatch
clock_skew
recovery_incomplete
certification_invalid
```

Kill switch behavior:

```text
HALT
```

must reject new exposure.

It must never be interpreted as:

```text
AUTO-LIQUIDATE
```

unless explicitly implemented and separately validated.

---

# 26. CERTIFICATION INTEGRATION

Prompt 23 is authoritative for certification.

Production paper/shadow operation must check:

```text
certification_status
```

before starting.

Example:

```text
CERTIFIED
CERTIFIED_WITH_VALID_WAIVERS
```

may run according to policy.

These must not silently run production shadow:

```text
DRAFT
UNDER_REVIEW
REJECTED
EXPIRED
REVOKED
```

No AI component may override certification.

---

# 27. MODEL / STRATEGY VERSION LOCK

Every cycle must identify:

```text
strategy_version
feature_version
factor_version
regime_version
model_version
adaptive_version
ensemble_version
capital_policy_version
execution_policy_version
risk_policy_version
```

Changing any production dependency creates a new configuration identity.

Never mutate historical production runs.

---

# 28. AI BOUNDARY

AI may:

```text
analyze
summarize
suggest
rank research hypotheses
explain diagnostics
```

AI may not:

```text
place orders
enable live trading
disable kill switches
change certification
change risk limits
modify frozen decisions
rewrite historical fills
alter reconciliation
promote itself
```

AI-generated content must be labelled:

```text
AI_SUGGESTION
```

and must not become evidence automatically.

---

# 29. BROKER BOUNDARY

Prompt 24 must contain:

```text
ZERO LIVE BROKER ROUTING
```

Do not import:

```text
kiteconnect
zerodha
openalgo
```

into the shadow package.

Do not create:

```text
BrokerAdapter
LiveOrderRouter
LiveOrderSubmitter
```

inside Prompt 24.

Prompt 23 remains certification/governance.

Future Prompt 25+ will establish controlled live execution architecture.

---

# 30. DATA SOURCES

Prompt 24 may consume:

```text
Prompt 20 production data
Prompt 04 PIT fabric
```

and user-supplied/current data sources approved by the existing data architecture.

The engine must distinguish:

```text
REAL
SYNTHETIC
SIMULATED
REPLAY
UNKNOWN
```

Synthetic data may run architecture tests.

Synthetic data must never be represented as:

```text
REAL_MARKET
```

---

# 31. PRODUCTION DATA QUALITY GATE

Before each cycle evaluate:

```text
schema
timestamp
availability
missingness
duplicates
symbol identity
corporate action state
calendar state
staleness
cross-source consistency
```

If critical quality fails:

```text
NO DECISION
```

unless policy explicitly defines a safe degraded mode.

---

# 32. DEGRADATION POLICY

Implement explicit degraded modes.

```text
NORMAL
DEGRADED_DATA
DEGRADED_EXECUTION
DEGRADED_MODEL
DEGRADED_ACCOUNT
HALTED
```

Do not silently substitute:

```text
zero
last value
future value
synthetic value
```

for missing critical information.

---

# 33. OBSERVABILITY

Expose:

```text
cycle latency
data latency
decision latency
execution latency
fill rate
partial fill rate
residual quantity
turnover
slippage
impact
spread
paper P&L
shadow P&L
tracking error
target drift
reconciliation status
data quality
model health
risk status
capital status
```

---

# 34. MONITORING INTEGRATION

Prompt 19 remains the authoritative monitoring engine.

Prompt 24 sends completed paper/shadow state into Prompt 19.

Do not create duplicate attribution logic.

Monitoring must distinguish:

```text
paper performance
shadow performance
actual broker performance
```

Actual broker performance must remain unavailable until a future controlled integration.

---

# 35. TCA INTEGRATION

Prompt 21 remains authoritative.

Prompt 24 must feed execution observations into TCA where valid.

Labels:

```text
OBSERVED
MODELLED
CALIBRATED
STRESSED
UNCALIBRATED
NOT_TESTED
```

must remain distinct.

Do not convert simulated TCA into observed broker TCA.

---

# 36. KNOWLEDGE GRAPH

Every meaningful production-paper event must be lineage-aware.

Add knowledge nodes such as:

```text
SHADOW_CYCLE
SHADOW_DECISION
SHADOW_ORDER
SHADOW_FILL
SHADOW_POSITION
SHADOW_RECONCILIATION
SHADOW_INCIDENT
SHADOW_ABSTENTION
```

Link:

```text
strategy
→ decision
→ target
→ order
→ fill
→ position
→ monitoring
→ TCA
→ incident
```

Failed cycles and abstentions must be preserved.

---

# 37. LEDGER

Reuse the canonical JSONL ledger.

Do not create a second ledger.

Add optional fields:

```text
shadow_cycle_id
shadow_order_id
shadow_fill_id
shadow_mode
market_snapshot_hash
paper_account_id
shadow_account_id
reconciliation_hash
production_run
data_freshness_ms
decision_latency_ms
execution_latency_ms
```

Existing rows must remain backward compatible.

---

# 38. INCIDENT MANAGEMENT

Create explicit incidents:

```text
DATA_STALE
DATA_CONFLICT
SYMBOL_UNRESOLVED
CALENDAR_UNKNOWN
MODEL_FAILURE
RISK_BREACH
CAPITAL_FAILURE
EXECUTION_FAILURE
RECONCILIATION_BREAK
CHECKPOINT_CORRUPTION
CLOCK_SKEW
CERTIFICATION_EXPIRED
UNSAFE_CONFIGURATION
```

Every incident must have:

```text
incident_id
timestamp
severity
source
description
state
resolution
lineage
```

No incident may be silently deleted.

---

# 39. HEARTBEAT

Implement a production heartbeat.

Expose:

```text
last_cycle
last_success
last_data
last_reconciliation
last_checkpoint
last_health_check
```

A dead process must be distinguishable from:

```text
healthy but idle
```

---

# 40. HEALTH MODEL

Add health components:

```text
shadow_engine
shadow_scheduler
production_data
snapshot_manager
decision_pipeline
paper_oms
execution_research
paper_accounting
reconciliation
monitoring
tca
knowledge
ledger
certification
safety
```

Each must expose:

```text
HEALTHY
DEGRADED
FAILED
UNKNOWN
```

---

# 41. CLI

Implement:

```text
quantlab shadow list
quantlab shadow inspect <cycle_id>
quantlab shadow start
quantlab shadow stop
quantlab shadow pause
quantlab shadow resume
quantlab shadow status
quantlab shadow run
quantlab shadow cycle
quantlab shadow decision
quantlab shadow targets
quantlab shadow orders
quantlab shadow fills
quantlab shadow positions
quantlab shadow cash
quantlab shadow reconcile
quantlab shadow health
quantlab shadow incidents
quantlab shadow latency
quantlab shadow drift
quantlab shadow tca
quantlab shadow compare
quantlab shadow checkpoint
quantlab shadow recover
quantlab shadow audit
quantlab shadow report
```

Research aliases:

```text
quantlab research shadow
quantlab research paper-production
quantlab research shadow-execution
quantlab research decision-drift
quantlab research production-fragility
quantlab research shadow-tca
quantlab research shadow-reconciliation
```

---

# 42. DESKTOP

Add:

```text
Shadow Trading Lab
```

to the desktop application.

The UI is a viewer/controller through:

```text
quantlab.app
```

Qt must NOT:

- parse Parquet
- query DuckDB directly
- calculate alpha
- fit models
- calculate allocations
- simulate fills
- modify paper state
- write ledger records
- bypass certification
- bypass safety
- connect to brokers

Recommended panels:

```text
SYSTEM STATUS
MARKET STATUS
DATA FRESHNESS
CURRENT DECISION
TARGET PORTFOLIO
SHADOW ORDERS
PAPER FILLS
POSITIONS
P&L
TCA
RECONCILIATION
LATENCY
INCIDENTS
CERTIFICATION
AUDIT TRAIL
```

Required badges:

```text
PAPER
SHADOW
LIVE DISABLED
NO BROKER ROUTING
```

Never show:

```text
LIVE
BROKER CONFIRMED
ORDER SENT
```

for shadow events.

---

# 43. SECURITY

Prompt 24 must not store broker credentials.

Reject environment variables such as:

```text
BROKER_PASSWORD
LIVE_ACCOUNT_ID
LIVE_ORDER_TOKEN
```

for the shadow execution path if their presence could cause ambiguity.

The safest behavior is:

```text
SHADOW_MODE = TRUE
LIVE_TRADING = FALSE
```

and hard assertion:

```python
assert live_trading is False
```

---

# 44. CONFIGURATION

Create an immutable configuration identity.

Include:

```text
mode
cycle_frequency
market
data_source
freshness_limits
risk_policy
capital_policy
execution_policy
slippage_policy
latency_policy
certification_id
strategy_version
model_versions
```

Hash:

```text
configuration_hash
```

Configuration changes must create a new run identity.

---

# 45. INTEGRITY CHECKS

Add explicit checks.

Unset:

```text
NOT_TESTED
```

Direct violation:

```text
FAIL
```

Required checks include:

```text
future_shadow_data
future_decision_input
future_execution_input
stale_data_decision
unknown_calendar_execution
duplicate_cycle
duplicate_shadow_order
shadow_live_confusion
live_route_attempt
paper_shadow_state_confusion
target_mutation
decision_mutation
snapshot_mutation
model_version_mutation
configuration_mutation
pre_arrival_shadow_fill
future_shadow_fill
partial_fill_hidden
shadow_accounting_break
shadow_reconciliation_break
checkpoint_hash_mismatch
recovery_without_reconciliation
certification_expired
certification_bypass
kill_switch_bypass
risk_bypass
ai_safety_override
synthetic_production_confusion
observed_tca_confusion
broker_confirmation_confusion
```

---

# 46. FAILURE SEMANTICS

Never convert failures into successful results.

Examples:

```text
NO DATA → ABSTAIN
STALE DATA → ABSTAIN / HALT
UNKNOWN CALENDAR → ABSTAIN
RISK FAIL → REJECT
CAPITAL FAIL → ABSTAIN
EXECUTION UNKNOWN → NOT_TESTED
RECON BREAK → HALT
CERTIFICATION INVALID → HALT
LIVE ROUTE ATTEMPT → FAIL + SAFETY HALT
```

---

# 47. DETERMINISM

For replayable cycles:

```text
same snapshot
+
same configuration
+
same strategy/model versions
+
same paper state
```

must produce:

```text
same decision_hash
same target_hash
same shadow_order_hash
same fill_hash
same reconciliation_hash
```

unless the execution model is explicitly stochastic.

If stochastic:

```text
random_seed
```

must be recorded.

---

# 48. REPLAY

Implement deterministic replay:

```text
quantlab shadow replay <cycle_id>
```

Replay must operate from the frozen snapshot.

It must not silently fetch future market data.

Compare:

```text
original decision
vs
replayed decision
```

and report:

```text
MATCH
MISMATCH
```

A mismatch must be investigated, not overwritten.

---

# 49. SHADOW-vs-PAPER ANALYSIS

Implement comparison metrics:

```text
decision agreement
target-weight difference
order difference
fill difference
slippage difference
turnover difference
P&L difference
drawdown difference
exposure difference
reconciliation difference
latency difference
```

This is a diagnostic system, not a promotion gate.

Prompt 05 remains the research gate.

Prompt 23 remains certification authority.

---

# 50. PRODUCTION READINESS SCORECARD

Create a diagnostic scorecard:

```text
DATA
PIT
MODEL
RISK
CAPITAL
EXECUTION
RECONCILIATION
MONITORING
TCA
CERTIFICATION
SAFETY
RECOVERY
OBSERVABILITY
```

Each component must report:

```text
PASS
WARN
FAIL
NOT_TESTED
```

Do not collapse these into a single “ready” boolean.

---

# 51. PAPER PERFORMANCE IS NOT MARKET EVIDENCE

The system must explicitly distinguish:

```text
RESEARCH RESULT
PAPER RESULT
SHADOW RESULT
BROKER OBSERVATION
LIVE RESULT
```

Prompt 24 must never claim:

```text
paper profit = validated alpha
```

or:

```text
shadow execution = broker execution
```

---

# 52. SYNTHETIC DATA

Synthetic data may be used for:

```text
unit tests
integration tests
recovery tests
determinism tests
state-machine tests
UI tests
architecture diagnostics
```

Synthetic results must remain:

```text
WARN
```

and must never become:

```text
RESEARCH_CANDIDATE
PROMOTED_TO_PAPER
CERTIFIED_FOR_LIVE
```

solely because the simulation performs well.

---

# 53. TEST SUITE

Create:

```text
tests/shadow/
```

Minimum coverage:

### Data

- stale-data rejection
- availability-time enforcement
- future-data rejection
- duplicate-data handling
- timestamp consistency

### Cycle

- deterministic cycle identity
- duplicate cycle prevention
- state transitions
- failure propagation

### Decision

- PIT decision
- frozen snapshot
- model-version locking
- target immutability

### Execution

- next-bar / arrival semantics
- latency
- spread
- slippage
- impact
- partial fills
- residuals

### Accounting

- cash identity
- position identity
- equity identity
- P&L

### Reconciliation

- exact match
- unexplained difference
- hash mismatch
- recovery reconciliation

### Safety

- live mode impossible
- broker imports absent
- AI cannot route
- kill-switch enforcement
- certification enforcement

### Recovery

- crash/restart
- checkpoint restore
- corrupted checkpoint
- duplicate replay

### UI

- offscreen smoke
- correct badges
- no live-order affordance

---

# 54. BROKER IMPORT AUDIT

Run a static audit ensuring:

```text
quantlab.shadow
```

does not import:

```text
kiteconnect
zerodha
openalgo
quantlab.brokers
```

Any violation must fail the build/test.

---

# 55. PERFORMANCE

The shadow engine must not block the desktop UI.

Use:

```text
background process
or
controlled worker
```

for long-running production cycles.

The UI remains a client of:

```text
quantlab.app
```

---

# 56. NO SECOND ENGINES

Explicitly reuse:

```text
Prompt 04 → data fabric
Prompt 05 → validation/gate
Prompt 07 → portfolio
Prompt 08 → risk/covariance
Prompt 09 → regime
Prompt 10 → adaptive
Prompt 11 → statistical learning
Prompt 12 → ensemble
Prompt 13 → execution research
Prompt 14 → orchestration
Prompt 15 → discovery
Prompt 16 → knowledge
Prompt 17 → capital
Prompt 18 → paper OMS
Prompt 19 → monitoring
Prompt 20 → production data
Prompt 21 → TCA
Prompt 22 → econometrics
Prompt 23 → certification
```

Prompt 24 is the **operational composition layer**.

---

# 57. DOCUMENTATION

Create:

```text
docs/decisions/ADR-038-production-paper-shadow-engine.md

docs/architecture/PRODUCTION_PAPER_SHADOW_ENGINE.md

docs/architecture/SHADOW_EXECUTION_ARCHITECTURE.md

docs/research/PRODUCTION_PAPER_TRADING.md

docs/research/SHADOW_EXECUTION.md

docs/research/SHADOW_VALIDATION.md

docs/operations/SHADOW_OPERATIONS_RUNBOOK.md

docs/operations/SHADOW_INCIDENT_RESPONSE.md

docs/operations/SHADOW_RECOVERY.md
```

Update:

```text
README.md
BACKLOG.md
LOCAL_RUN.md
architecture map
health registry
desktop navigation
knowledge documentation
```

---

# 58. VERSION

Update:

```text
__version__ = "2.4.0"
```

Update the project version consistently.

---

# 59. ACCEPTANCE CRITERIA

Prompt 24 is complete only if:

```text
[ ] Production/current market data can feed the existing PIT fabric
[ ] Decision cycles are deterministic and identifiable
[ ] Every cycle has an immutable snapshot
[ ] Data freshness is enforced
[ ] Session/calendar state is explicit
[ ] Target portfolio is generated by existing capital engine
[ ] Orders use existing Paper OMS semantics
[ ] Shadow orders are distinct from broker orders
[ ] Execution uses existing execution-research models
[ ] Partial fills are visible
[ ] Residuals are preserved
[ ] Paper accounting reconciles
[ ] Shadow state reconciles
[ ] Restart/recovery is implemented
[ ] Kill switch is implemented
[ ] Certification state is enforced
[ ] AI cannot override safety
[ ] No broker imports exist
[ ] LIVE_TRADING remains false
[ ] No live order API exists
[ ] Existing ledger remains authoritative
[ ] Existing knowledge graph remains authoritative
[ ] Existing TCA remains authoritative
[ ] Existing monitoring remains authoritative
[ ] Existing research gate remains authoritative
[ ] Replay works
[ ] Idempotency works
[ ] Integrity checks work
[ ] UI is query/control-only
[ ] Full audit trail exists
[ ] Synthetic data remains clearly labelled
```

---

# 60. REQUIRED TEST COMMANDS

At minimum:

```bash
pytest tests/shadow

ruff check src/quantlab/shadow tests/shadow

mypy --strict src/quantlab/shadow
```

Regression:

```bash
pytest
```

Health:

```bash
quantlab shadow health
```

Safety audit:

```bash
quantlab shadow audit
```

Dry production paper cycle:

```bash
quantlab shadow run --mode paper
```

Shadow cycle:

```bash
quantlab shadow run --mode shadow
```

Replay:

```bash
quantlab shadow replay <cycle_id>
```

Reconciliation:

```bash
quantlab shadow reconcile
```

---

# 61. FINAL SAFETY ASSERTIONS

The implementation must end with automated assertions equivalent to:

```python
assert LiveSafetyGates().live_trading is False
assert shadow_mode is True
assert broker_routing_enabled is False
assert live_order_submission_enabled is False
```

A production paper/shadow process must fail closed if any of these assumptions are violated.

---

# 62. FINAL ARCHITECTURE

After Prompt 24 the QUANT LAB architecture should be:

```text
                    ┌──────────────────────────────┐
                    │      PRODUCTION DATA         │
                    │       Prompt 20              │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │        PIT DATA FABRIC        │
                    │       Prompt 04               │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │      RESEARCH STACK           │
                    │      Prompts 06–16            │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │     VALIDATION / GATE          │
                    │ Prompts 05 + 23                │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │      CAPITAL ALLOCATION        │
                    │       Prompt 17                │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │          PAPER OMS             │
                    │       Prompt 18                │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
              ╔════════════════════════════════════════════╗
              ║       PROMPT 24 — SHADOW ENGINE           ║
              ║                                            ║
              ║  LIVE DATA → DECISION → TARGET →           ║
              ║  SHADOW ORDER → SIMULATED FILL →           ║
              ║  PAPER/SHADOW STATE → RECONCILIATION      ║
              ║                                            ║
              ║             LIVE ROUTING: OFF              ║
              ╚══════════════════════╤═════════════════════╝
                                     │
                  ┌──────────────────┼──────────────────┐
                  ▼                  ▼                  ▼
             Monitoring             TCA             Knowledge
             Prompt 19           Prompt 21           Prompt 16
                  │                  │                  │
                  └──────────────────┼──────────────────┘
                                     ▼
                            AUDIT / OPERATIONS
                                     │
                                     ▼
                         ┌────────────────────────┐
                         │   LIVE BROKER LAYER    │
                         │      NOT ENABLED       │
                         │      FUTURE PHASE      │
                         └────────────────────────┘
```

---

# 63. ENGINEERING PHILOSOPHY

The implementation must follow these principles:

```text
FAIL CLOSED
NO SILENT FALLBACKS
NO FUTURE INFORMATION
NO HIDDEN STATE
NO MUTABLE HISTORY
NO DUPLICATE ENGINES
NO UNVERIFIED ASSUMPTIONS
NO SYNTHETIC MARKET CLAIMS
NO BROKER ROUTING
NO AI OVERRIDE
NO AUTOMATIC PROMOTION
```

The purpose of Prompt 24 is not to make QUANT LAB “trade.”

The purpose is to prove, under **real production market conditions and without risking capital**, that the complete research → decision → allocation → execution → accounting → monitoring → reconciliation pipeline behaves correctly, reproducibly, observably, and safely.

Only after this layer demonstrates sustained operational correctness should the architecture proceed toward a controlled broker abstraction and eventual restricted live execution.

---

# END OF PROMPT 24

**QUANT LAB 2.4.0**

**Production Paper Trading & Shadow Execution Engine**

**LIVE_TRADING = FALSE**

**NO LIVE ORDER ROUTING**
