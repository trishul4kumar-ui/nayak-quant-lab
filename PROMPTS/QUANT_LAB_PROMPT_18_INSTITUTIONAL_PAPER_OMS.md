# QUANT LAB — PROMPT 18
# Institutional Paper OMS & Order Lifecycle Control Engine

**Target Release:** QUANT LAB 1.8.0  
**Prompt:** 18  
**Status:** Implementation specification  
**Priority:** CRITICAL  
**Execution Mode:** PAPER ONLY  
**Live Trading:** MUST remain `false`

---

## 0. CODING-AGENT DIRECTIVE

You are implementing **Prompt 18** on the existing QUANT LAB 1.7.0 codebase.

This is an **institutional-grade Paper Order Management System (Paper OMS)**.

Do NOT rewrite, fork, duplicate, or replace any existing engine.

You MUST preserve the architecture established by Prompts 01–17.

The Paper OMS is the controlled boundary between:

```text
RESEARCH / INVESTMENT DECISION
              ↓
        TARGET PORTFOLIO
              ↓
        ─────────────
          PROMPT 18
          PAPER OMS
        ─────────────
              ↓
       PAPER ORDERS
              ↓
       PAPER FILLS
              ↓
        PAPER POSITIONS
              ↓
        RECONCILIATION
```

It MUST NOT connect to a live broker.

It MUST NOT import:

```text
kiteconnect
zerodha
openalgo
broker SDKs
broker credentials
quantlab.brokers
```

from the Paper OMS package.

---

# 1. PRIMARY RESEARCH / ENGINEERING QUESTION

Prompt 18 answers:

> **Given an immutable investment decision and target portfolio, what orders would be required, how would those orders transition through an OMS lifecycle, what would actually fill under paper execution assumptions, what positions/cash would result, and whether the resulting state reconciles exactly with the recorded order/fill history?**

The engine must distinguish:

```text
Target Portfolio
≠
Order Intent
≠
Order Plan
≠
Paper Order
≠
Paper Fill
≠
Position
≠
Broker Confirmation
```

A paper fill is NEVER represented as a real market execution.

---

# 2. NON-NEGOTIABLE ARCHITECTURAL PRINCIPLES

## 2.1 One P&L engine

Prompt 18 MUST NOT create a second backtester.

Existing:

```text
quantlab.backtest.run_backtest
```

remains the canonical research P&L engine.

Paper OMS performs order lifecycle simulation and paper accounting only.

If an existing canonical accounting component can be reused, reuse it.

---

## 2.2 One execution-research engine

Prompt 13 remains the canonical source for:

- spread assumptions
- slippage
- impact
- liquidity
- latency
- partial-fill assumptions
- execution costs
- capacity diagnostics

Prompt 18 MUST consume those abstractions rather than creating competing execution formulas.

---

## 2.3 One research gate

Prompt 05 remains the only research promotion gate.

Paper OMS MUST NOT promote:

```text
WARN → RESEARCH_CANDIDATE
RESEARCH_CANDIDATE → PAPER
PAPER → LIVE
```

It may reject an input that is not eligible for paper execution, but it cannot change the research gate.

---

## 2.4 Capital allocation remains Prompt 17

Prompt 17 remains authoritative for:

- capital policy
- investment decision
- target weights
- capital budgets
- risk budgets
- sizing
- abstention

Prompt 18 converts an approved target into order planning.

It MUST NOT silently resize an investment decision.

If the target is infeasible:

```text
REJECT
```

or produce an explicit residual.

Never silently modify it.

---

# 3. DOMAIN SEPARATION

Maintain the following ontology:

```text
DATA
FEATURE
FACTOR
ALPHA
REGIME
MODEL
ADAPTIVE LEARNER
ENSEMBLE
PORTFOLIO
RESEARCH EXPERIMENT
RESEARCH EVIDENCE
CAPITAL POLICY
INVESTMENT DECISION
TARGET PORTFOLIO
ORDER INTENT
ORDER PLAN
PAPER ORDER
PAPER FILL
POSITION
CASH
RECONCILIATION
```

No class may collapse these concepts merely because they contain similar fields.

---

# 4. PACKAGE ARCHITECTURE

Create a thin, isolated package:

```text
src/quantlab/paper_oms/
```

Recommended structure:

```text
paper_oms/
├── __init__.py
├── models.py
├── enums.py
├── policy.py
├── intent.py
├── planner.py
├── orders.py
├── lifecycle.py
├── fills.py
├── execution.py
├── positions.py
├── accounting.py
├── reconciliation.py
├── idempotency.py
├── events.py
├── state.py
├── validation.py
├── repository.py
├── service.py
├── reporting.py
└── cli.py
```

Keep `__init__.py` thin.

Do not import the UI from the domain package.

Do not import brokers.

---

# 5. CORE DOMAIN OBJECTS

Implement strongly typed immutable or controlled-state domain models.

At minimum:

```text
OrderIntent
OrderPlan
PaperOrder
PaperFill
OrderEvent
Position
CashLedger
PaperAccount
ReconciliationReport
OMSState
OMSRun
```

---

# 6. ORDER INTENT

`OrderIntent` represents the desired change implied by an approved target portfolio.

Required provenance:

```text
decision_id
decision_hash
target_portfolio_id
target_portfolio_hash
capital_policy_id
experiment_id
snapshot_id
as_of
```

Required economic fields:

```text
security_id
side
target_weight
current_weight
weight_delta
target_quantity
current_quantity
delta_quantity
estimated_notional
```

Order intent MUST be derived from the immutable target portfolio.

It cannot modify the target portfolio.

---

# 7. ORDER PLAN

`OrderPlan` transforms order intents into executable paper instructions.

Required fields:

```text
order_plan_id
order_plan_hash
decision_hash
intent_hash
snapshot_id
planning_time
execution_policy_id
```

Each plan must specify:

```text
security_id
side
quantity
order_type
limit_price
reference_price
time_in_force
expected_arrival
expected_fill_policy
```

The plan MUST be deterministic.

Same:

```text
decision
+
account state
+
market snapshot
+
execution policy
```

must produce the same plan.

---

# 8. PAPER ORDER MODEL

Implement an explicit order lifecycle.

Suggested states:

```text
CREATED
    ↓
VALIDATED
    ↓
PLANNED
    ↓
SUBMITTED_PAPER
    ↓
ACKNOWLEDGED
    ↓
PARTIALLY_FILLED
    ↓
FILLED
    ↓
RECONCILED
```

Terminal states:

```text
REJECTED
CANCELLED
EXPIRED
FAILED
```

Invalid transitions MUST raise a typed error.

Do not permit arbitrary state mutation.

---

# 9. ORDER EVENT SOURCING

Every lifecycle transition must generate an immutable event.

Example:

```text
OrderCreated
OrderValidated
OrderSubmittedPaper
PaperFillReceived
OrderPartiallyFilled
OrderFilled
OrderCancelled
OrderRejected
OrderExpired
OrderReconciled
```

Each event should contain:

```text
event_id
order_id
event_type
event_time
sequence_number
previous_state
new_state
payload_hash
causation_id
correlation_id
```

The event sequence must be auditable.

---

# 10. IDEMPOTENCY

This is mandatory.

The same investment decision MUST NOT create duplicate paper orders when processed twice.

Implement deterministic idempotency keys.

Examples:

```text
decision_hash
order_intent_hash
order_plan_hash
idempotency_key
```

Repeated submission:

```text
same input
→ same identity
→ existing result returned
```

not:

```text
same input
→ duplicate order
```

Test duplicate processing explicitly.

---

# 11. TARGET → ORDER DIFFERENCE

Order planning must calculate:

```text
Δw = target_weight - current_weight
```

and:

```text
Δq = target_quantity - current_quantity
```

with explicit rounding policy.

Never use:

```text
target_weight > 0 → BUY
target_weight < 0 → SELL
```

without comparing against current holdings.

The system must correctly support:

```text
BUY
SELL
INCREASE
DECREASE
EXIT
NO_ACTION
ABSTAIN
```

---

# 12. ROUNDING & RESIDUALS

Quantity rounding must be explicit.

Do not silently round away economic exposure.

Record:

```text
requested_quantity
rounded_quantity
residual_quantity
residual_notional
rounding_policy
```

Residual target exposure must remain visible.

---

# 13. PAPER EXECUTION

Paper execution MUST use Prompt 13 execution-research abstractions.

Support at minimum:

```text
base
conservative
high_slippage
wide_spread
high_impact
low_liquidity
high_latency
partial_fill
stressed
```

Do not invent an independent execution model.

---

# 14. PAPER FILL MODEL

A paper fill must contain:

```text
fill_id
order_id
security_id
side
requested_quantity
filled_quantity
remaining_quantity
reference_price
execution_price
gross_notional
commission
taxes
fees
spread_cost
slippage_cost
impact_cost
total_cost
arrival_time
fill_time
latency
liquidity_status
execution_model_id
```

Explicitly distinguish:

```text
reference price
arrival price
simulated execution price
```

Never label a simulated execution price as a broker-confirmed execution.

---

# 15. PARTIAL FILLS

Partial fills are mandatory.

Never assume:

```text
requested_quantity == filled_quantity
```

Support:

```text
PARTIALLY_FILLED
remaining_quantity
residual_order
CANCELLED_REMAINDER
EXPIRED_REMAINDER
```

Example:

```text
requested = 10,000
filled = 6,000
remaining = 4,000
```

The system must preserve the 4,000-share residual.

---

# 16. LATENCY

Execution must respect:

```text
decision_time
order_creation_time
arrival_time
fill_time
```

No fill may occur before arrival.

A future price cannot be used merely because it is available in the dataset.

Reuse Prompt 13 latency semantics.

---

# 17. PAPER ACCOUNT

Implement explicit paper accounting.

Never define capital as merely:

```text
portfolio market value
```

Maintain:

```text
cash
reserved_cash
available_cash
gross_exposure
net_exposure
market_value
equity
realized_pnl
unrealized_pnl
fees
slippage
impact
turnover
```

Cash movements must be deterministic.

---

# 18. POSITION ACCOUNTING

Each position should maintain:

```text
security_id
quantity
average_cost
market_price
market_value
realized_pnl
unrealized_pnl
gross_exposure
weight
last_update
```

Support:

```text
flat
long
short
```

only where Prompt 17's policy permits it.

Do not silently enable shorting.

---

# 19. ACCOUNTING INVARIANTS

Implement hard accounting invariants.

For example:

```text
cash + market_value - liabilities = equity
```

subject to the exact accounting convention selected.

Also verify:

```text
opening_cash
+ deposits
- purchases
+ sales
- fees
= closing_cash
```

and:

```text
requested_qty
=
filled_qty
+
remaining_qty
+
cancelled_qty
+
expired_qty
```

within explicitly documented lifecycle semantics.

Any broken invariant must be:

```text
FAIL
```

not warning-only.

---

# 20. RECONCILIATION ENGINE

This is one of the most important components.

The OMS must reconcile:

```text
Target Portfolio
       ↕
Order Intent
       ↕
Order Plan
       ↕
Paper Orders
       ↕
Paper Fills
       ↕
Positions
       ↕
Cash
```

Produce:

```text
ReconciliationReport
```

with:

```text
status
target_difference
order_difference
fill_difference
position_difference
cash_difference
unexplained_difference
```

Statuses:

```text
RECONCILED
RECONCILIATION_BREAK
NOT_TESTED
```

Never silently repair a discrepancy.

---

# 21. RECONCILIATION BREAKS

Examples:

```text
missing order
missing fill
duplicate fill
quantity mismatch
price mismatch
cash mismatch
position mismatch
orphan event
event sequence break
target/order mismatch
order/fill mismatch
```

Every break must be retained.

A break cannot be deleted merely because the next run succeeds.

---

# 22. POSITION TARGET RECONCILIATION

Compare:

```text
TargetPortfolio
vs
PaperPosition
```

for every security.

Report:

```text
target_weight
actual_weight
weight_error
target_quantity
actual_quantity
quantity_error
notional_error
```

Use explicit tolerances.

Do not hide small residuals.

---

# 23. ORDER VALIDATION

Before submission to the paper simulator, validate:

```text
security exists
quantity > 0
side valid
price valid
cash sufficient
reserved cash sufficient
position sufficient for sell
shorting permitted
instrument tradable
market session valid
order type valid
time-in-force valid
risk limits satisfied
execution policy valid
```

A failed validation produces a typed rejection.

---

# 24. RISK FIREWALL

Prompt 18 MUST respect the existing `RiskFirewall`.

If:

```text
HALT
EMERGENCY
```

then new exposure MUST be rejected.

Existing positions may still be represented and reconciled.

Prompt 18 does not automatically liquidate unless an explicit paper policy says so.

---

# 25. SAFETY GATE

Implement a hard paper-only safety gate.

The following must fail:

```text
live_trading=True
live broker adapter
broker credentials
live order submission
production account
```

Suggested invariant:

```python
assert_live_trading_disabled()
```

If a live flag is ever enabled:

```text
SafetyError
```

must be raised before order creation or submission.

---

# 26. BROKER ISOLATION

Paper OMS must have zero dependency on:

```text
Zerodha
Kite Connect
OpenAlgo
broker credentials
broker sessions
broker network clients
```

The future architecture is:

```text
Paper OMS
     ↓
Broker Interface
     ↓
Zerodha Adapter
```

but Prompt 18 MUST NOT implement the live adapter.

---

# 27. FUTURE BROKER CONTRACT

You may define a future-neutral protocol/interface such as:

```text
BrokerAdapter
```

but the Paper OMS must use:

```text
PaperExecutionAdapter
```

or equivalent.

Do not import or instantiate a real broker.

---

# 28. MARKET SESSION MODEL

Reuse the existing calendar/data semantics.

Do not invent official NSE holidays.

If official holiday information is unavailable:

```text
NOT_TESTED
```

not PASS.

Order session validation must remain explicit.

---

# 29. CORPORATE ACTIONS

Do not fabricate corporate-action events.

If an adjustment is unknown:

```text
UNKNOWN
NOT_TESTED
```

and preserve the original observation.

Do not silently alter historical positions.

---

# 30. LEDGER INTEGRATION

Reuse the existing JSONL research ledger.

Paper OMS should append provenance such as:

```text
selection_stage="paper_oms"
oms_run_id
decision_hash
order_plan_hash
execution_policy_id
paper_account_id
reconciliation_hash
```

Do not create a competing ledger.

---

# 31. KNOWLEDGE GRAPH INTEGRATION

Prompt 16 knowledge memory should retain:

```text
INVESTMENT_DECISION
TARGET_PORTFOLIO
ORDER_INTENT
ORDER_PLAN
PAPER_ORDER
PAPER_FILL
RECONCILIATION
```

with explicit lineage:

```text
decision
  ↓
target
  ↓
intent
  ↓
order plan
  ↓
paper order
  ↓
fill
  ↓
position
  ↓
reconciliation
```

Failed orders and reconciliation breaks must remain searchable.

---

# 32. HASHING & IMMUTABILITY

Hash:

```text
OrderIntent
OrderPlan
PaperOrder
PaperFill
ReconciliationReport
OMSRun
```

Hashes must be deterministic.

Hash inputs must be canonicalized.

Do not include nondeterministic dictionary ordering.

Do not include mutable timestamps in an identity hash unless the timestamp is part of the object's immutable identity.

---

# 33. OMS RUN

Implement:

```text
OMSRun
```

with:

```text
oms_run_id
decision_hash
snapshot_id
account_id
execution_policy_id
started_at
completed_at
status
order_count
fill_count
reconciliation_status
run_hash
```

Same deterministic inputs should produce reproducible paper results.

---

# 34. FAILURE HANDLING

Failures must be explicit.

Suggested classes:

```text
OMSValidationError
InvalidOrderTransition
DuplicateOrderError
InsufficientCashError
InsufficientPositionError
PaperSafetyError
ReconciliationError
AccountingInvariantError
OrderPlanningError
UnsupportedOrderTypeError
```

Do not catch broad exceptions and convert them to PASS/WARN.

---

# 35. INTEGRITY FLAGS

Extend the existing integrity system.

New checks should include at minimum:

```text
target_mutation
decision_hash_mismatch
order_intent_mutation
order_plan_mutation
duplicate_order
duplicate_fill
invalid_order_transition
pre_arrival_fill
future_execution_price
future_fill_information
future_liquidity_leak
full_fill_assumption
hidden_partial_fill
cash_accounting_break
position_accounting_break
target_position_mismatch
order_fill_mismatch
orphan_fill
orphan_event
reconciliation_break
execution_policy_mutation
paper_live_mode_confusion
broker_import_violation
```

Semantics:

```text
None → NOT_TESTED
true leak / violation → FAIL
verified invariant → PASS
```

Do not convert unknown information into PASS.

---

# 36. ADV / LIQUIDITY

Use Prompt 13 semantics.

Unknown liquidity must not mean infinite liquidity.

If volume is unavailable:

```text
unfilled
or
NOT_TESTED
```

according to the execution policy.

Do not fabricate ADV.

---

# 37. TRANSACTION COSTS

Reuse Prompt 05 / Prompt 13 cost abstractions.

Default research cost assumptions remain explicit.

Do not invent Indian tax/fee schedules.

For unspecified:

```text
provenance = "unspecified"
status = NOT_TESTED
```

---

# 38. PAPER TCA

Provide execution attribution:

```text
gross target notional
filled notional
spread drag
slippage drag
impact drag
commission
other specified fees
total execution drag
residual target
```

Compute:

```text
implementation_shortfall
```

only when all required inputs are valid.

Otherwise:

```text
NOT_TESTED
```

---

# 39. ORDER REPORTING

Implement reports for:

```text
order lifecycle
fill report
position report
cash report
TCA
reconciliation
residual targets
rejections
exceptions
```

Reports must be deterministic and auditable.

---

# 40. CLI

Add:

```text
quantlab paper list
quantlab paper inspect <id>
quantlab paper create
quantlab paper plan <decision>
quantlab paper validate <plan>
quantlab paper submit <plan>
quantlab paper fills <run>
quantlab paper positions <account>
quantlab paper cash <account>
quantlab paper reconcile <run>
quantlab paper orders <run>
quantlab paper events <order>
quantlab paper cancel <order>
quantlab paper report <run>
quantlab paper tca <run>
quantlab paper residuals <run>
quantlab paper exceptions <run>
quantlab paper audit <run>
```

Research aliases:

```text
quantlab research paper-oms
quantlab research paper-execution
quantlab research order-lifecycle
quantlab research reconciliation
quantlab research paper-tca
```

Existing commands must remain unchanged.

---

# 41. APPLICATION SERVICE

Create:

```text
quantlab.app.paper_oms
```

Responsibilities:

- expose query/use-case services to UI
- create paper runs
- retrieve orders
- retrieve fills
- retrieve positions
- retrieve reconciliation
- expose reports

It must not contain Qt code.

---

# 42. DESKTOP — PAPER OMS LAB

Add:

```text
Paper OMS Lab
```

to the desktop.

The UI is a viewer/controller of `quantlab.app`.

It must NOT:

```text
parse Parquet
query DuckDB directly
compute target portfolios
fit models
run GP
modify investment decisions
mutate orders directly
import brokers
store credentials
```

Show:

```text
OMS status
Paper account
Target portfolio
Order plan
Order lifecycle
Fills
Positions
Cash
TCA
Residuals
Reconciliation
Exceptions
Audit trail
```

Use explicit status badges:

```text
PAPER
LIVE DISABLED
RECONCILED / BREAK
```

Never display a paper fill as:

```text
LIVE FILLED
BROKER CONFIRMED
```

---

# 43. UI SAFETY

The desktop must make the paper/live distinction visually unambiguous.

There must be no button labelled:

```text
BUY
SELL
PLACE LIVE ORDER
```

that could plausibly invoke a real broker.

Use:

```text
SIMULATE ORDER
SUBMIT PAPER
CANCEL PAPER
```

for Prompt 18.

---

# 44. PAPER ACCOUNT RESET

Account reset must be explicit.

Never silently reset paper state.

A reset should produce:

```text
reset_id
previous_state_hash
new_state_hash
reason
timestamp
```

and an audit event.

---

# 45. PERSISTENCE

Use the existing project's persistence conventions.

Do not introduce a heavyweight database unless required.

Paper OMS state must survive application restart.

Do not rely solely on in-memory state.

---

# 46. CONCURRENCY

Protect against duplicate simultaneous submission.

At minimum test:

```text
same order submitted twice
same plan submitted twice
same decision processed concurrently
```

Expected result:

```text
one logical paper order
```

not two.

---

# 47. DETERMINISM TEST

Given:

```text
same decision
same account
same snapshot
same execution policy
same random seed
```

produce:

```text
same order intent hash
same order plan hash
same simulated fill result
same reconciliation result
```

If stochastic simulation is introduced, the seed must be explicit and recorded.

---

# 48. RANDOMNESS

No hidden randomness.

If partial fills, latency, or execution uncertainty uses randomness:

```text
random_seed
distribution
parameters
```

must be part of the immutable execution policy.

---

# 49. SECURITY

Paper OMS must never accept:

```text
API_KEY
API_SECRET
ACCESS_TOKEN
BROKER_PASSWORD
LIVE_ACCOUNT_ID
```

as required configuration.

If such variables are detected in a paper execution path, fail closed.

---

# 50. TEST MATRIX

Create:

```text
tests/paper_oms/
```

Minimum coverage:

### Domain

- intent construction
- order planning
- order identity
- lifecycle transitions
- invalid transitions
- partial fills
- residual quantities
- position accounting
- cash accounting

### Safety

- live flag rejected
- broker imports absent
- credentials rejected
- live order path impossible

### Idempotency

- duplicate decision
- duplicate plan
- duplicate order
- duplicate fill

### Execution

- spread
- slippage
- impact
- latency
- partial fills
- insufficient liquidity
- rejected order

### Reconciliation

- clean reconciliation
- quantity mismatch
- price mismatch
- cash mismatch
- position mismatch
- orphan fill
- orphan event
- duplicate fill

### Determinism

- identical inputs → identical hashes/results

### PIT

Appending future market data must not alter historical paper decisions or fills.

### Regression

All Prompts 01–17 tests must remain passing.

---

# 51. MINIMUM ACCEPTANCE CRITERIA

Prompt 18 is NOT complete unless:

```text
1. TargetPortfolio → OrderIntent works.
2. OrderIntent → OrderPlan works.
3. OrderPlan → PaperOrder works.
4. PaperOrder lifecycle is state-machine controlled.
5. Partial fills work.
6. Residual quantities remain visible.
7. Cash accounting works.
8. Position accounting works.
9. Reconciliation works.
10. Idempotency works.
11. Deterministic hashes work.
12. Prompt 13 execution models are reused.
13. Prompt 05 remains the only gate.
14. Prompt 17 remains authoritative for allocation.
15. No live broker import exists.
16. LIVE_TRADING remains false.
17. UI remains paper-only.
18. JSONL ledger lineage is preserved.
19. Knowledge graph lineage is preserved.
20. Integrity failures are explicit.
```

---

# 52. REQUIRED REGRESSION COMMANDS

Run at minimum:

```bash
ruff check src tests
mypy --strict src/quantlab
pytest
quantlab slice
quantlab backtest run
quantlab validate run
quantlab research gate <experiment>
quantlab capital validate
quantlab paper list
```

All existing functionality must remain intact.

---

# 53. VERSION

Update:

```text
__version__ = "1.8.0"
```

Update:

```text
pyproject.toml
README
BACKLOG
LOCAL_RUN
architecture map
```

---

# 54. DOCUMENTATION

Create:

```text
docs/decisions/ADR-032-paper-oms.md

docs/architecture/PAPER_OMS_ARCHITECTURE.md
docs/architecture/ORDER_LIFECYCLE.md
docs/architecture/PAPER_ACCOUNTING.md
docs/architecture/RECONCILIATION_ENGINE.md
docs/research/PAPER_EXECUTION.md
docs/research/PAPER_TCA.md
docs/development/PAPER_OMS_LOCAL_RUN.md
```

Document all invariants.

Document every intentional limitation.

---

# 55. ARCHITECTURAL MAP

Update the architecture map:

```text
PROMPT 17
CAPITAL ALLOCATION
      ↓
INVESTMENT DECISION
      ↓
TARGET PORTFOLIO
      │
      │  HARD BOUNDARY
      ▼
┌──────────────────────────────┐
│       PROMPT 18              │
│       PAPER OMS              │
│                              │
│ Target → Intent              │
│ Intent → Order Plan          │
│ Plan → Paper Order           │
│ Order → Paper Fill           │
│ Fill → Position              │
│ Position → Reconciliation    │
└──────────────┬───────────────┘
               ↓
        PAPER ACCOUNT
               ↓
          PAPER TCA
               ↓
         AUDIT / LEDGER
               │
               X
        LIVE BROKER
        NOT CONNECTED
```

---

# 56. EXPLICIT NON-GOALS

Do NOT implement:

```text
Zerodha integration
Kite Connect
OpenAlgo live routing
live orders
live credentials
live portfolio
broker authentication
broker websocket
production OMS
automatic liquidation
real-money execution
```

Those belong to future controlled phases.

---

# 57. WHAT PROMPT 18 MUST NOT BECOME

Do not allow the Paper OMS to become:

```text
a second backtester
a portfolio optimizer
an alpha engine
a risk model
a research gate
a broker adapter
an AI trader
a live OMS
```

Its responsibility is:

```text
ORDER LIFECYCLE + PAPER EXECUTION STATE + ACCOUNTING + RECONCILIATION
```

---

# 58. INSTITUTIONAL CONTROL PRINCIPLE

The system must be able to answer, for every paper order:

> Why was this order created?

Answer through:

```text
order
← order plan
← order intent
← target portfolio
← investment decision
← capital policy
← research result
← experiment
← hypothesis
← evidence
← PIT snapshot
```

And:

> What happened to it?

Answer through:

```text
order events
→ paper fills
→ cash movements
→ position state
→ reconciliation
→ TCA
→ ledger
→ knowledge graph
```

Nothing may exist without provenance.

---

# 59. FAILURE IS DATA

The following are valid research outcomes:

```text
ORDER_REJECTED
INSUFFICIENT_CASH
INSUFFICIENT_LIQUIDITY
PARTIAL_FILL
EXECUTION_FRAGILITY
RECONCILIATION_BREAK
ACCOUNTING_BREAK
TARGET_RESIDUAL
STALE_DECISION
RISK_HALT
```

Do not hide failures.

Do not convert them into successful paper results.

---

# 60. FINAL SAFETY INVARIANT

At the end of Prompt 18 implementation, this must remain true:

```python
LiveSafetyGates().live_trading is False
```

and:

```text
TargetPortfolio
      ↓
Paper OMS
      ↓
Paper Order
      ↓
Paper Fill
      ↓
Position
```

must terminate entirely inside the local paper environment.

There must be **no executable path to Zerodha** from Prompt 18.

---

# 61. DEFINITION OF DONE

Prompt 18 is complete only when the coding agent can demonstrate:

```text
RESEARCH GATE
      ↓
CAPITAL ALLOCATION
      ↓
INVESTMENT DECISION
      ↓
TARGET PORTFOLIO
      ↓
ORDER INTENT
      ↓
ORDER PLAN
      ↓
PAPER ORDER
      ↓
PAPER FILL
      ↓
POSITION
      ↓
CASH
      ↓
RECONCILIATION
      ↓
TCA
      ↓
LEDGER + KNOWLEDGE
```

with:

```text
PIT integrity              PASS / NOT_TESTED honestly
Determinism                 PASS
Idempotency                 PASS
Accounting invariants       PASS
Order lifecycle             PASS
Partial-fill handling       PASS
Reconciliation              PASS
Safety gate                 PASS
Broker isolation            PASS
Existing regression         PASS
LIVE_TRADING                FALSE
```

A paper system that cannot reconcile itself is NOT a valid paper OMS.

A paper fill that cannot be traced to a target decision is NOT a valid institutional research artifact.

A system that can accidentally reach a broker is NOT complete.

---

# 62. FINAL ENGINEERING DIRECTIVE

Implement Prompt 18 **on top of the existing QUANT LAB architecture**.

Do not simplify the specification merely to make tests pass.

Do not create fake implementations solely for UI demonstration.

Do not fabricate NSE market data, liquidity, holidays, broker fills, or transaction costs.

Do not claim production readiness.

Use explicit:

```text
PASS
WARN
FAIL
NOT_TESTED
```

where appropriate.

Preserve all previous invariants.

Run the complete regression suite.

Fix all errors introduced by Prompt 18.

Do not weaken existing tests to obtain a green build.

Do not delete failed experiments, failed orders, reconciliation breaks, or historical evidence.

The objective is not to make QUANT LAB look like a trading terminal.

The objective is to build an **auditable, deterministic, fail-closed institutional paper OMS that can eventually serve as the controlled proving ground before any broker integration is permitted.**

## END OF PROMPT 18
