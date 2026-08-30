# QUANT LAB — PROMPT 31
# Institutional Deterministic Shadow Validation, Replay & Trading Digital Twin Engine

**Target Version:** 3.1.0  
**Primary Package:** `quantlab.digital_twin`  
**ADR:** ADR-043  
**Safety:** SHADOW ONLY — ZERO BROKER WRITE

## Mission

Build the deterministic proving environment for QUANT LAB's real-time system.

Question:

> If QUANT LAB had operated at time T with exactly the information and system state available then, what would it have decided, what would simulated execution produce, and can the complete result be reproduced exactly?

```text
SHADOW ≠ PAPER ≠ LIVE
REPLAY ≠ RESEARCH REWRITE
DIGITAL TWIN ≠ BROKER
SIMULATED FILL ≠ BROKER CONFIRMATION
```

## Architecture

```text
P29 Real-Time Data
      ↓
P30 Real-Time Decision
      ↓
TargetPortfolio
      ↓
P18 Paper OMS
      ↓
P13 Execution Research
      ↓
P21 TCA
      ↓
DIGITAL TWIN
      ↓
Shadow State
      ↓
Monitoring / Reconciliation / Replay
```

Compose existing engines. Do not create duplicate OMS, TCA, backtester, risk, portfolio or ledger implementations.

## Twin State

Represent:

```text
Market State
Strategy Release
Research State
Portfolio State
Capital State
Risk State
Execution Policy
Paper Account
System State
```

Never represent the twin as the real broker account.

## Modes

```text
HISTORICAL_REPLAY
REALTIME_SHADOW
PAPER_REPLAY
FAILURE_INJECTION
COUNTERFACTUAL
DETERMINISM_TEST
```

All remain non-routable.

## Shadow Lifecycle

```text
OBSERVE → FREEZE → DECIDE → PLAN → SIMULATE
→ ACCOUNT → RECONCILE → MONITOR → REPLAY → COMPARE
```

Every stage produces immutable evidence.

## Event Sourcing

Use immutable events such as:

```text
MarketObserved
SnapshotFrozen
DecisionGenerated
DecisionAbstained
TargetPortfolioCreated
OrderIntentCreated
PaperOrderPlanned
PaperFillGenerated
PositionChanged
CashChanged
RiskChanged
ReconciliationPerformed
MonitoringSnapshotCreated
```

Every event contains:

```text
event_id
event_type
event_time
sequence
run_id
parent_event_id
payload_hash
state_hash_before
state_hash_after
```

No silent overwrites.

## Replay

Given:

```text
initial_state
event_log
strategy_release
configuration
```

replay must reproduce:

```text
state hashes
decisions
target portfolios
paper fills
cash
positions
reconciliation
```

Any unexplained mismatch is `REPLAY_MISMATCH`.

## Historical Information Boundary

Replay must preserve:

```text
available_time <= replay_time
```

No complete future dataset may be used to reconstruct a historical decision.

## Checkpoints

Create checkpoints at:

- session start
- decision boundary
- order-plan boundary
- fill boundary
- session close
- exception
- halt
- reconciliation

Each checkpoint includes relevant snapshot, release, decision, portfolio, account, risk, execution-policy and state hashes.

## Determinism

Two identical replays must produce identical:

```text
decision_hash
state_hash
portfolio_hash
fill_hash
account_hash
reconciliation_hash
```

Difference without an approved nondeterministic source is failure.

## Failure Injection

Support controlled scenarios:

```text
feed_disconnect
stale_market
sequence_gap
clock_jump
missing_volume
missing_quote
model_unavailable
risk_data_missing
portfolio_infeasible
paper_fill_failure
duplicate_fill
out_of_order_event
reconciliation_break
disk_pressure
process_restart
```

Expected responses are explicit:

```text
DEGRADE | ABSTAIN | HALT | RECONCILE | RECOVER
```

Fatal states do not silently resume.

## Crash / Recovery

Test:

```text
process crash
→ restart
→ restore checkpoint
→ replay events
→ reconcile
```

Recovered canonical state must match the pre-crash state.

## Counterfactuals

Allow controlled changes to:

- spread
- latency
- impact
- capital
- risk limits
- execution policy

Every result is labelled:

```text
COUNTERFACTUAL
NOT OBSERVED
NOT MARKET EVIDENCE
```

Counterfactual data must never contaminate observed shadow results.

## Monitoring / TCA

Reuse Prompt 19 and Prompt 21.

Track P&L, drawdown, turnover, exposure, attribution, residuals, shortfall and capacity diagnostics.

Never treat shadow P&L as proof of alpha.

## Reconciliation

Perform:

```text
Decision reconciliation
Execution reconciliation
Account reconciliation
```

Unexplained differences become `RECONCILIATION_BREAK`. Never silently repair them.

## Certification

Consume Prompt 23/27 status. This engine does not certify itself.

Invalid/expired/revoked certification must block or downgrade production-like shadow according to policy.

## Knowledge / Ledger

Use existing Prompt 16 knowledge and JSONL ledger.

Lineage:

```text
StrategyRelease
→ ShadowRun
→ Decision
→ ExecutionSimulation
→ Monitoring
→ TCA
→ Reconciliation
```

Preserve failures and dead ends.

## Integrity Flags

```text
future_replay_input
future_shadow_state
replay_snapshot_mismatch
replay_state_mutation
replay_nondeterminism
event_order_violation
event_deletion
checkpoint_mutation
shadow_live_confusion
counterfactual_observation_confusion
simulated_fill_as_broker_fill
hidden_reconciliation_break
recovery_state_mismatch
release_mismatch
strategy_state_mismatch
shadow_routing_attempt
```

`None → NOT_TESTED`; direct leak → `FAIL`.

## CLI

```bash
quantlab twin list
quantlab twin inspect
quantlab twin create
quantlab twin run
quantlab twin pause
quantlab twin halt
quantlab twin checkpoint
quantlab twin replay
quantlab twin compare
quantlab twin reconcile
quantlab twin failures
quantlab twin recovery
quantlab twin determinism
quantlab twin counterfactual
quantlab twin report
quantlab twin audit
```

Research aliases:

```bash
quantlab research digital-twin
quantlab research shadow-validation
quantlab research deterministic-replay
quantlab research failure-injection
quantlab research recovery
quantlab research counterfactual
quantlab research shadow-drift
```

No command routes orders.

## Desktop

Create **Digital Twin / Shadow Lab**.

Allowed actions:

```text
RUN SHADOW
REPLAY
CHECKPOINT
RECONCILE
INJECT FAILURE
HALT
```

Forbidden:

```text
SEND ORDER
LIVE TRADE
BROKER ROUTE
```

## Testing

Mandatory:

- deterministic replay
- future isolation
- crash recovery
- checkpoint restoration
- failure injection
- reconciliation breaks
- counterfactual isolation
- shadow routing firewall
- state/event hash integrity
- UI smoke

Property:

```text
future_data_append → prior_state_unchanged
original_run == replay_run
```

## NOT_TESTED

Do not claim broker execution equivalence, real exchange latency, real order-book depth, institutional fill probability, calibrated impact, live alpha profitability or live capacity.

## Final Safety Boundary

```text
REAL-TIME DATA
      ↓
REAL-TIME DECISION
      ↓
TARGET PORTFOLIO
      ↓
DIGITAL TWIN
      ↓
SHADOW / REPLAY
      ↓
RECONCILIATION
      ↓
VALIDATED STATE

════════ HARD WALL ════════

BROKER EXECUTION
NOT PRESENT
```

Mandatory:

```text
LIVE_TRADING = false
BROKER_WRITE_ENABLED = false
```

Prompt 31 is complete only when the entire real-time decision → shadow → accounting → reconciliation → replay path is deterministic, auditable and non-routable.
