# QUANT LAB — PROMPT 35
# Institutional Live Shadow / Paper Validation & Production Readiness Engine

**Target Version:** 3.5.0 | **Package:** `quantlab.production_shadow` | **ADR:** ADR-049

## Mission
Run QUANT LAB against real market data and real Zerodha account observations while proving the complete decision loop without sending any order.

> If QUANT LAB were allowed to trade, what would it decide and what would simulated execution produce under observed market/account conditions?

## Absolute Boundary
```text
REAL MARKET DATA = YES
REAL BROKER OBSERVATION = YES
REAL-TIME DECISION = YES
SHADOW ORDERS = YES
SIMULATED FILLS = YES
BROKER WRITE = NO
LIVE ORDER = NO
```

## Architecture
```text
P34 Market Data
   ↓
P29 State
   ↓
P30 Decision
   ↓
P17 Target
   ├→ P18 Paper OMS → P13/P21 TCA
   └→ P32 Broker Read → P33 Reconciliation
                 ↓
              P31 Twin
                 ↓
             P19 Monitor
```

Compose existing engines. No second OMS, TCA, backtester, risk, portfolio, capital or ledger.

## Shadow Identity
Every run records:
```text
shadow_run_id
market_snapshot_hash
broker_snapshot_hash
strategy_release_hash
decision_hash
target_portfolio_hash
paper_order_plan_hash
execution_policy_hash
twin_state_hash
reconciliation_hash
```

## Time Alignment
Market and broker observations must be temporally aligned. Never compare unrelated timestamps without explicit policy.

## Decision Capture
Record exactly:
- available data
- active strategy release
- feature/model/ensemble state
- risk checks
- target portfolio
- abstentions

No broker order is submitted.

## Shadow Lifecycle
Reuse Prompt 18:
```text
TARGET → INTENT → PLAN → SIMULATED FILL → ACCOUNTING
```
with `NON_ROUTABLE=true`.

## Broker Comparison
Compare:
```text
actual broker position
vs
shadow target
vs
shadow simulated position
```
Differences are diagnostics, never trading instructions.

## Evidence Labels
Strictly distinguish:
```text
OBSERVED
COUNTERFACTUAL
SIMULATED
MODELLED
CALIBRATED
STRESSED
NOT_TESTED
```

## Monitoring / TCA
Reuse Prompts 19 and 21 for P&L, turnover, exposure, drawdown, TCA, capacity and drift. Shadow P&L is not proof of alpha.

## Drift
Monitor:
```text
feature drift
prediction drift
regime drift
portfolio drift
execution-cost drift
market-data drift
broker-state drift
```
Explicit responses:
```text
WARN | PAUSE | HALT
```

## Readiness Scorecard
Create evidence-backed readiness across:
```text
DATA
MODEL
ALPHA
RISK
PORTFOLIO
CAPITAL
EXECUTION
RECONCILIATION
OPERATIONS
SAFETY
CERTIFICATION
DETERMINISM
```
No aggregate score may conceal a critical failure. Do not invent minimum observation counts; make them policy-configurable and certified.

## Incidents
Immutable:
```text
incident_id
severity
detected_at
source
description
evidence
state
owner
resolution
```
States:
```text
OPEN | ACKNOWLEDGED | INVESTIGATING | MITIGATED | RESOLVED | ESCALATED
```

## Certification
Consume Prompt 23/27. Prompt 35 cannot certify or promote itself. Invalid/expired/revoked certification blocks or downgrades shadow operation.

## CLI
```bash
quantlab shadow-prod status
quantlab shadow-prod start
quantlab shadow-prod stop
quantlab shadow-prod run
quantlab shadow-prod health
quantlab shadow-prod decisions
quantlab shadow-prod orders
quantlab shadow-prod fills
quantlab shadow-prod drift
quantlab shadow-prod reconciliation
quantlab shadow-prod incidents
quantlab shadow-prod readiness
quantlab shadow-prod replay
quantlab shadow-prod audit
quantlab shadow-prod report
```

## Desktop
Create Production Shadow Lab with market feed, broker observation, release, decision, hypothetical orders, simulated fills, actual positions, reconciliation, drift, TCA, incidents, readiness and safety state.

Forbidden:
```text
SEND ORDER
ENABLE LIVE
ROUTE TO BROKER
```

## Integrity
```text
shadow_market_broker_time_mismatch
shadow_future_data
shadow_release_mismatch
shadow_decision_mutation
shadow_order_routing_attempt
shadow_simulated_fill_as_broker_fill
shadow_broker_state_confusion
shadow_reconciliation_break
shadow_drift_suppression
shadow_incident_deletion
shadow_readiness_bypass
shadow_certification_bypass
shadow_live_enable_attempt
shadow_counterfactual_contamination
```

## Testing
End-to-end mock market + broker fixtures must cover decision, paper OMS, TCA, reconciliation, twin and monitoring. Add market/broker disconnect, stale states, certification expiry, safety halt, mismatch, routing attempt, restart and deterministic replay tests.

## NOT_TESTED
Do not claim live profitability, execution equivalence, production alpha validation, institutional capacity or live readiness from shadow P&L alone.

## Final Acceptance
```text
REAL MARKET
   ↓
REAL ACCOUNT OBSERVATION
   ↓
REAL-TIME DECISION
   ↓
SHADOW ORDER
   ↓
SIMULATED EXECUTION
   ↓
RECONCILIATION
   ↓
MONITORING
   ↓
READINESS EVIDENCE
        ║
   HARD SAFETY WALL
        ║
BROKER WRITE = FALSE
LIVE TRADING = FALSE
```

Prompt 35 generates evidence for a future controlled execution decision; it does not grant that permission.
