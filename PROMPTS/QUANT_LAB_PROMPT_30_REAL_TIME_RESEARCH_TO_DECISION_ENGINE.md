# QUANT LAB — PROMPT 30
# Institutional Real-Time Research-to-Decision Engine

**Target Version:** 3.0.0  
**Primary Package:** `quantlab.realtime_decision`  
**ADR:** ADR-042  
**Safety:** DECISION-ONLY — NO BROKER EXECUTION

## Mission

Build the real-time inference layer that composes QUANT LAB's existing research engines with Prompt 29's frozen market state.

Question:

> Given only information available at real-world time T, what would the currently released research stack decide?

```text
MarketState(T)
 → Features
 → Alpha
 → Regime
 → Adaptive State
 → Model
 → Ensemble
 → Portfolio
 → Capital
 → Risk
 → InvestmentDecision
 → TargetPortfolio
```

`TargetPortfolio` is the terminal output. It is not an order.

## Architectural Rule

Compose existing engines; do not fork:

- Prompt 20 data/PIT
- Prompt 29 real-time state
- Prompt 06 alpha
- Prompt 07 portfolio
- Prompt 08 risk
- Prompt 09 regimes
- Prompt 10 adaptive learning
- Prompt 11 statistical learning
- Prompt 12 ensembles
- Prompt 14 orchestration
- Prompt 16 knowledge
- Prompt 17 capital
- Prompt 18 paper OMS
- Prompt 21 TCA
- Prompt 23 certification
- Prompt 25 safety
- Prompt 27 release governance

No second feature, covariance, portfolio, capital, gate or execution engine.

## Strategy Release

Every production-like decision must reference an immutable `StrategyRelease`:

```text
release_id
strategy_id
version
code_version
data_contract
feature_manifest
alpha_manifest
model_manifest
ensemble_manifest
regime_policy
portfolio_policy
capital_policy
risk_limits
execution_policy
certification_id
certification_status
release_hash
effective_at
expiry_at
```

Never load an implicit "latest" model.

## Decision Cycle

```text
OBSERVE → VALIDATE → FREEZE → FEATURE → ALPHA
→ REGIME → MODEL → ENSEMBLE → PORTFOLIO
→ CAPITAL → RISK → DECISION → AUDIT
```

A required-stage failure produces `ABSTAIN`, `BLOCK` or `HALT` according to policy. No improvised decision.

## Predict / Freeze Discipline

At T:

```text
observe
→ freeze MarketState
→ compute research inputs
→ freeze decision
→ persist hashes
```

No upstream object may mutate after downstream computation begins.

## Adaptive Learning

Reuse Prompt 10:

```text
PREDICT
→ FREEZE
→ REALIZE WHEN AVAILABLE
→ SCORE
→ UPDATE
```

Never update a learner before the information becomes available.

## Feature / Model Governance

Features must carry identity, version, formula hash, availability and snapshot identity.

Only certified model/release versions may be used for production-like decisions. Unknown, expired or uncertified releases cause abstention/block.

## Regime Governance

Predictive regimes must be trained under valid walk-forward constraints. Full-sample smoothing/hindsight regimes fail integrity.

## Decision Object

Create immutable `RealTimeDecision`:

```text
decision_id
decision_time
snapshot_id
snapshot_hash
release_id
feature_manifest_hash
alpha_manifest_hash
model_manifest_hash
ensemble_manifest_hash
regime_state
portfolio_id
capital_policy_id
risk_state
target_portfolio
abstentions
diagnostics
decision_hash
```

## State Machine

```text
OBSERVING
VALIDATING
READY
COMPUTING
DECIDED
ABSTAINED
BLOCKED
STALE
HALTED
ERROR
```

Illegal transitions must fail.

## Abstention

First-class reasons include:

- stale market data
- missing critical feature
- invalid state
- unavailable model
- expired certification
- risk breach
- infeasible portfolio
- insufficient liquidity evidence
- TCA failure
- clock failure
- session uncertainty
- safety block

The system must be comfortable producing `NO DECISION`.

## Risk / Capital / Execution

Reuse Prompt 08 risk and Prompt 17 capital. Hard constraints remain hard.

Prompt 13/21 execution/TCA is diagnostic only. It cannot create live authorization.

## AI Boundary

AI may emit `AI_SUGGESTION` for research and diagnostics.

AI may not certify, promote, authorize, override safety/risk, or create live orders.

## Determinism

Same:

```text
snapshot + release + configuration + seed + adaptive state
```

must produce the same `decision_hash`.

## Ledger / Knowledge

Use the existing JSONL ledger and Prompt 16 knowledge graph. Preserve complete lineage:

```text
snapshot → feature → alpha → model → ensemble
→ portfolio → capital → risk → decision
```

Do not create a second ledger.

## Integrity Flags

```text
future_realtime_feature
future_realtime_model
future_realtime_regime
future_adaptive_update
release_mutation
uncertified_model_use
expired_release_use
decision_state_mutation
snapshot_mismatch
stale_state_decision
missing_critical_input
risk_bypass
capital_constraint_bypass
safety_bypass
decision_replay_mismatch
ai_authority_violation
```

`None → NOT_TESTED`; direct leak → `FAIL`.

## CLI

```bash
quantlab realtime-decision status
quantlab realtime-decision releases
quantlab realtime-decision inspect
quantlab realtime-decision run
quantlab realtime-decision explain
quantlab realtime-decision abstentions
quantlab realtime-decision risk
quantlab realtime-decision exposure
quantlab realtime-decision portfolio
quantlab realtime-decision replay
quantlab realtime-decision audit
quantlab realtime-decision lineage
```

Research aliases:

```bash
quantlab research realtime
quantlab research realtime-decision
quantlab research decision-replay
quantlab research decision-stability
quantlab research decision-abstention
```

No order routing.

## Desktop

Create **Real-Time Decision Lab** as a query/view layer. Show release, state, decision, target portfolio, diagnostics, risk, abstentions, lineage, hashes and safety state.

No order controls.

## Testing

Mandatory tests for PIT availability, future isolation, stale inputs, missing features, certification, release expiry, model mutation, regime leakage, adaptive ordering, risk blocks, capital infeasibility, deterministic replay, abstention, concurrency, snapshot mismatch and AI authority denial.

## NOT_TESTED

Do not claim live alpha profitability, real exchange latency, production capacity, calibrated impact, broker execution quality, or market evidence from synthetic/replay diagnostics.

## Acceptance

```text
LIVE_TRADING = false
BROKER_WRITE_ENABLED = false
Decision ≠ Order
TargetPortfolio ≠ OrderIntent
AI ≠ Authority
RealTime ≠ LiveExecution
```

No broker imports and no live authorization.
