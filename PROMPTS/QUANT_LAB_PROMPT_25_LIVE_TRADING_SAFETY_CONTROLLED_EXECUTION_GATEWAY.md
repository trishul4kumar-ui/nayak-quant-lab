# QUANT LAB — PROMPT 25
# Live Trading Safety & Controlled Execution Gateway
## Institutional-Grade Engineering Specification
### Target Release: QUANT LAB 2.5.0

---

## 0. Mission

Implement Prompt 25 as the **Live Trading Safety & Controlled Execution Gateway**.

This engine is the final deterministic safety boundary between a certified shadow/paper research system and any future broker-routing layer.

The gateway must answer:

> **If an execution request is ever presented to the live boundary, is it authorized, valid, reconciled, risk-compliant, operationally healthy, and safe to release — or must it be rejected?**

This is a **safety gateway, not a broker adapter, not an OMS, not a strategy engine, and not an alpha engine**.

### Non-negotiable state

```text
LIVE_TRADING = FALSE
```

Prompt 25 must NOT enable actual broker execution.

Any future live path must remain impossible until Prompt 27 certification and the explicitly approved future broker-integration boundary are satisfied.

---

# 1. Architectural Position

```text
P01–P16 Research
        ↓
P17 Capital Allocation
        ↓
P18 Paper OMS
        ↓
P19 Monitoring
        ↓
P20 Production Data
        ↓
P21 TCA / Capacity
        ↓
P22 Econometrics
        ↓
P23 Independent Validation / Certification
        ↓
P24 Paper / Shadow Execution
        ↓
┌──────────────────────────────────────────────┐
│ P25 LIVE TRADING SAFETY & CONTROLLED GATEWAY │
│                                              │
│ AUTHORIZATION                                │
│ ORDER SAFETY                                 │
│ RISK LIMITS                                  │
│ STATE / HEALTH                               │
│ RECONCILIATION                               │
│ KILL SWITCH                                  │
│ DUPLICATION / IDEMPOTENCY                    │
│ AUDIT / EVIDENCE                             │
└──────────────────────────────────────────────┘
        ↓
     FUTURE BROKER
        ↓
P26 Operational Control Plane
        ↓
P27 Live Trading Certification / Promotion
```

Do not move broker implementation into Prompt 25.

---

# 2. Hard Architectural Rules

1. Prompt 25 must not contain strategy logic.
2. Prompt 25 must not generate alpha.
3. Prompt 25 must not modify portfolio targets.
4. Prompt 25 must not bypass Prompt 05 research gating.
5. Prompt 25 must not bypass Prompt 23 certification.
6. Prompt 25 must not bypass Prompt 24 shadow evidence.
7. Prompt 25 must not create broker credentials.
8. Prompt 25 must not import `kiteconnect`, `zerodha`, `openalgo`, or broker SDKs.
9. Prompt 25 must not place a live order.
10. `LIVE_TRADING=false` remains the default and enforced state.
11. Safety failure must fail closed.
12. Unknown safety state must never be interpreted as safe.
13. Missing evidence must be `NOT_TESTED`, never fabricated as PASS.
14. Emergency controls must have higher authority than strategy decisions.
15. AI/LLM components must never override safety controls.
16. No automatic recovery from a safety halt without explicit authorization.
17. Every authorization decision must be deterministic, versioned, hashed, and auditable.
18. The gateway must reject stale, mutated, duplicated, or unverifiable execution requests.

---

# 3. Critical Conceptual Separation

```text
ALPHA
  ≠
MODEL
  ≠
PORTFOLIO
  ≠
TARGET PORTFOLIO
  ≠
ORDER INTENT
  ≠
PAPER ORDER
  ≠
SHADOW ORDER
  ≠
LIVE EXECUTION REQUEST
  ≠
BROKER ORDER
```

Prompt 25 owns the **decision to allow or reject crossing the controlled execution boundary**.

It does not own the broker.

---

# 4. Execution Safety State Machine

Implement an explicit state machine.

Suggested states:

```text
DISABLED
↓
RESEARCH_ONLY
↓
PAPER
↓
SHADOW
↓
ARMED
↓
AUTHORIZED
↓
RELEASE_BLOCKED
↓
HALTED
↓
EMERGENCY
↓
RECOVERY_PENDING
```

The exact state transition graph must be explicit.

Illegal transitions must raise a typed exception.

Examples:

```text
RESEARCH_ONLY → AUTHORIZED       = INVALID
PAPER → LIVE_RELEASE             = INVALID
HALTED → AUTHORIZED              = INVALID
EMERGENCY → AUTHORIZED           = INVALID
DISABLED → ARMED                 = INVALID
```

Recovery must require explicit evidence and authorization.

---

# 5. Authorization Model

Create a typed `ExecutionAuthorization` object.

It must include at minimum:

```text
authorization_id
decision_hash
target_portfolio_hash
order_plan_hash
paper/shadow evidence reference
certification reference
risk snapshot reference
data snapshot reference
TCA policy reference
account identity
execution policy identity
system state
authorization timestamp
expiry timestamp
authorization version
nonce
authorization hash
```

Authorization must be immutable.

Changing any material input invalidates the authorization.

---

# 6. Multi-Layer Safety Gates

Implement independent gates.

Suggested hierarchy:

```text
G0 Configuration Gate
G1 Mode Gate
G2 Certification Gate
G3 Data Freshness Gate
G4 Decision Integrity Gate
G5 Order Integrity Gate
G6 Risk Limit Gate
G7 Capital Gate
G8 Liquidity / Capacity Gate
G9 TCA Gate
G10 Account-State Gate
G11 Reconciliation Gate
G12 Operational Health Gate
G13 Kill-Switch Gate
G14 Human Authorization Gate
G15 Final Release Gate
```

Every gate returns a typed result:

```text
PASS
WARN
BLOCK
NOT_TESTED
EMERGENCY
```

`BLOCK`, `EMERGENCY`, and critical `NOT_TESTED` must prevent release.

Warnings must never silently become authorization.

---

# 7. Fail-Closed Principle

Implement:

```text
SAFE_TO_RELEASE =
    ALL_REQUIRED_GATES_PASS
    AND
    LIVE_MODE_EXPLICITLY_AUTHORIZED
    AND
    CERTIFICATION_VALID
    AND
    RECONCILIATION_HEALTHY
    AND
    ACCOUNT_STATE_VALID
    AND
    KILL_SWITCH_OFF
```

If any required information is unavailable:

```text
UNKNOWN → BLOCK
```

Never:

```text
UNKNOWN → PASS
```

---

# 8. Kill Switch

Implement a first-class kill-switch system.

Required controls:

```text
GLOBAL_KILL
ACCOUNT_KILL
STRATEGY_KILL
SYMBOL_KILL
BUY_KILL
SELL_KILL
NEW_ORDER_KILL
MODIFY_ORDER_KILL
CANCEL_ORDER_KILL
LIVE_RELEASE_KILL
```

Kill switches must have:

```text
switch_id
scope
reason
created_at
created_by
activation_source
state
timestamp
audit_hash
```

Activation must be fail-safe.

A kill switch may block trading but must never itself create an order.

---

# 9. Risk Controls

Reuse Prompt 08 and Prompt 17 risk infrastructure.

Do not build a second risk engine.

Support checks for:

- gross exposure
- net exposure
- position concentration
- single-name concentration
- portfolio leverage
- turnover
- capital budget
- drawdown state
- factor exposure where PIT-valid
- volatility target
- liquidity constraints
- capacity constraints
- order notional
- participation rate
- price sanity
- quantity sanity

Hard violations:

```text
REJECT
```

Do not silently reduce an order unless the policy explicitly permits deterministic clipping.

If clipping is permitted, preserve:

```text
requested_qty
approved_qty
residual_qty
clipping_reason
policy_hash
```

---

# 10. Order Safety

Validate:

```text
symbol identity
security_id
side
quantity
price
order type
time-in-force
target
current position
delta
maximum order quantity
minimum tick
minimum lot
notional
cash requirement
available buying power
duplicate status
staleness
authorization
```

Reject:

- negative quantity
- invalid side
- unknown security
- stale decision
- stale authorization
- mutated decision
- duplicate request
- inconsistent target
- impossible cash state
- impossible position state
- unauthorized order type
- invalid price
- invalid tick size
- limit violation

---

# 11. Price and Market Data Safety

Prompt 25 may consume Prompt 20/24 market-state evidence.

It must validate:

```text
timestamp freshness
snapshot identity
security identity
price plausibility
trading-session state
market-open state
data-quality state
corporate-action state
```

Future information must never influence authorization.

If the required market snapshot is unavailable:

```text
BLOCK
```

Do not use the latest available price merely because it exists.

---

# 12. Account-State Safety

Future broker account state will be represented through a broker-neutral protocol.

Define interfaces only.

Example conceptual protocol:

```text
AccountStateProvider
PositionStateProvider
BalanceStateProvider
OrderStateProvider
FillStateProvider
```

Prompt 25 may consume account-state evidence but must not implement a broker-specific connector.

---

# 13. Reconciliation Barrier

No release may occur while the previous state is unreconciled.

Required statuses:

```text
RECONCILED
PENDING
MISMATCH
UNKNOWN
EMERGENCY
```

Rules:

```text
MISMATCH → BLOCK
UNKNOWN → BLOCK
EMERGENCY → BLOCK
```

Do not auto-repair discrepancies.

Preserve:

```text
expected_state
observed_state
difference
reconciliation_hash
timestamp
```

---

# 14. Staleness Controls

Define explicit TTL policies for:

- decision
- target portfolio
- order plan
- market snapshot
- account state
- risk state
- certification
- authorization
- TCA evidence
- operational health

Expired objects must not be reused.

---

# 15. Idempotency

Every execution request requires an idempotency key.

Repeated identical requests must return the same authorization/rejection record.

Conflicting reuse of an idempotency key must be rejected.

No duplicate release may be possible through retry.

---

# 16. Audit Ledger

Reuse the existing JSONL ledger architecture.

Do not create an unrelated ledger.

Record:

```text
authorization
gate results
risk checks
kill-switch state
account state reference
reconciliation reference
decision hash
order plan hash
policy hash
system state
actor
timestamp
outcome
reason
```

Every blocked request must remain auditable.

---

# 17. AI Boundary

AI may:

- summarize
- classify research evidence
- propose diagnostics
- explain a rejection
- surface anomalies

AI may NOT:

- override a gate
- disable kill switches
- modify risk limits
- authorize live execution
- create authorization signatures
- alter certification
- alter reconciliation
- convert WARN to PASS
- convert NOT_TESTED to PASS

Explicitly test these invariants.

---

# 18. Human Authorization

Design a future-ready human approval boundary.

It must support:

```text
actor_id
role
authorization_scope
reason
timestamp
expiry
two-person approval where policy requires
```

Do not implement insecure placeholder authentication.

If identity cannot be verified:

```text
BLOCK
```

---

# 19. Emergency Semantics

Emergency mode must:

- block new exposure
- block unauthorized modification
- preserve state
- preserve audit trail
- expose reconciliation status
- prevent automatic return to normal operation

Do not implement automatic liquidation in Prompt 25 unless explicitly delegated by a future certified policy.

---

# 20. Package Architecture

Create:

```text
src/quantlab/safety/
    __init__.py
    authorization.py
    gates.py
    gate_results.py
    state.py
    transitions.py
    kill_switch.py
    risk_checks.py
    order_checks.py
    market_checks.py
    account_checks.py
    reconciliation.py
    staleness.py
    idempotency.py
    audit.py
    human_authorization.py
    emergency.py
    policy.py
    service.py
    repository.py
    models.py
    errors.py
    integrity.py
    cli.py
```

Keep `__init__.py` thin.

No broker imports.

---

# 21. Application Layer

Add:

```text
quantlab.app.safety
```

Responsibilities:

- safety status
- authorization requests
- gate evaluation
- kill-switch state
- audit queries
- operational summaries

No Qt logic.

---

# 22. Desktop

Add **Safety & Control Lab**.

Qt is a viewer/controller through `quantlab.app`.

It must NOT:

- calculate risk
- modify safety policy directly
- import brokers
- bypass authorization
- alter ledger records
- create hidden approvals

UI must make dangerous states visually unambiguous:

```text
LIVE DISABLED
BLOCKED
HALTED
EMERGENCY
RECONCILIATION BREAK
CERTIFICATION EXPIRED
DATA STALE
```

---

# 23. CLI

Implement:

```text
quantlab safety status
quantlab safety inspect
quantlab safety gates
quantlab safety authorize
quantlab safety reject
quantlab safety kill
quantlab safety unkill
quantlab safety halt
quantlab safety emergency
quantlab safety recover
quantlab safety reconcile
quantlab safety audit
quantlab safety policy
quantlab safety validate
quantlab safety explain
```

Default behavior must remain non-live.

---

# 24. Integrity Flags

Add explicit flags where appropriate:

```text
unauthorized_release
missing_authorization
stale_authorization
future_account_state
future_market_state
future_risk_state
decision_hash_mismatch
target_hash_mismatch
order_plan_hash_mismatch
certification_expired
certification_mismatch
reconciliation_break
kill_switch_bypass
risk_limit_bypass
stale_decision
duplicate_release
idempotency_collision
invalid_safety_transition
unknown_safety_state
ai_safety_override
human_authorization_missing
policy_mutation
audit_mutation
emergency_bypass
```

Rules:

```text
None → NOT_TESTED
Direct leak / bypass → FAIL
Critical unknown → BLOCK
```

---

# 25. Determinism

Given identical:

```text
decision
target
order plan
account state
market state
risk state
certification
policy
safety state
```

the gateway must produce the same:

```text
gate results
authorization decision
decision hash
authorization hash
```

---

# 26. Tests

Minimum test families:

```text
tests/safety/
    test_authorization.py
    test_gates.py
    test_state_machine.py
    test_kill_switch.py
    test_risk_checks.py
    test_order_checks.py
    test_staleness.py
    test_reconciliation.py
    test_idempotency.py
    test_ai_boundary.py
    test_emergency.py
    test_integrity.py
    test_determinism.py
    test_cli.py
```

Mandatory tests:

1. `LIVE_TRADING=false` cannot authorize live release.
2. Missing certification blocks.
3. Expired certification blocks.
4. Failed research gate blocks.
5. Failed reconciliation blocks.
6. Active kill switch blocks.
7. Unknown risk state blocks.
8. Stale decision blocks.
9. Mutated target invalidates authorization.
10. Duplicate request is idempotent.
11. Conflicting idempotency key is rejected.
12. AI cannot override.
13. Human authorization cannot bypass safety gates.
14. Emergency state cannot transition directly to authorized.
15. Future account state does not affect historical authorization.
16. Future market state does not affect historical authorization.
17. Negative quantities reject.
18. Invalid symbols reject.
19. Excess concentration rejects.
20. Cash insufficiency rejects.
21. Audit records are immutable.
22. Policy mutation invalidates authorization.
23. Broker imports are absent.
24. UI cannot bypass app-layer controls.

---

# 27. Verification Requirements

Run:

```text
pytest tests/safety
ruff check <owned paths>
mypy --strict <owned paths>
```

Also run regression suites for:

```text
paper_oms
capital
monitoring
tca
data
certification
shadow
integrity
knowledge
UI smoke
```

Expected:

```text
LIVE_TRADING = false
BROKER_IMPORTS = 0
UNKNOWN_SAFETY_STATE = BLOCK
```

---

# 28. Documentation

Create:

```text
docs/architecture/LIVE_TRADING_SAFETY_GATEWAY.md
docs/architecture/EXECUTION_AUTHORIZATION.md
docs/architecture/SAFETY_STATE_MACHINE.md
docs/architecture/KILL_SWITCH_ARCHITECTURE.md
docs/architecture/EXECUTION_SAFETY_POLICY.md
docs/research/LIVE_BOUNDARY.md
docs/decisions/ADR-038-live-trading-safety-gateway.md
```

Update:

```text
README
BACKLOG
LOCAL_RUN
architecture map
health registry
CLI documentation
```

---

# 29. Forbidden Shortcuts

Do NOT:

- add a broker adapter
- call Zerodha
- import Kite Connect
- create live credentials
- create a live order
- silently downgrade safety
- auto-approve unknown state
- auto-repair reconciliation
- create a second risk engine
- create a second ledger
- create a second backtester
- let UI bypass application services
- let AI override safety
- treat paper/shadow fills as broker confirmations

---

# 30. Completion Criteria

Prompt 25 is complete only when:

```text
[ ] Safety gateway exists
[ ] Explicit state machine exists
[ ] Multi-layer gates exist
[ ] Authorization is immutable + hashed
[ ] Kill switches exist
[ ] Reconciliation is a hard barrier
[ ] Staleness controls exist
[ ] Idempotency exists
[ ] AI cannot override
[ ] Human authorization boundary exists
[ ] Emergency mode exists
[ ] Audit trail exists
[ ] Integrity flags exist
[ ] Desktop Safety Lab exists
[ ] CLI exists
[ ] No broker imports
[ ] LIVE_TRADING=false
[ ] Existing engines remain intact
[ ] Regression tests pass
[ ] ruff clean on owned paths
[ ] mypy strict clean on owned paths
[ ] Documentation complete
```

### Final Principle

> **The system must be easier to stop than to start, easier to reject than to authorize, and impossible to route live merely because a strategy wants to trade.**

Prompt 25 is a **safety boundary**, not permission to trade.
