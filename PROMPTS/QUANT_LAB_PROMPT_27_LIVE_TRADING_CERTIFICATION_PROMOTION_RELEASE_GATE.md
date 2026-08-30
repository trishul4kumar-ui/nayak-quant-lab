# QUANT LAB — PROMPT 27
# Institutional Live Trading Certification, Promotion & Release Gate

**Target Version:** 2.7.0  
**Status:** Engineering Specification  
**Scope:** Governance, certification, promotion, release authorization  
**Critical Rule:** `CERTIFIED ≠ LIVE_ENABLED ≠ BROKER_CONNECTED`

---

## 1. Mission

Build an institutional-grade **Live Trading Certification, Promotion & Release Gate** on top of QUANT LAB 2.6.0.

The engine must answer:

> **Has QUANT LAB accumulated sufficient independent evidence, validation, operational readiness, safety evidence, execution evidence, reconciliation evidence, and governance approvals to make a controlled live release eligible?**

This is a **certification and governance engine**.

It is **not**:
- a strategy engine
- an alpha engine
- a portfolio constructor
- a broker adapter
- an OMS
- an execution engine
- an authorization bypass
- an AI trading agent

Prompt 27 must not place, modify, cancel, or route a broker order.

---

## 2. Non-Negotiable Safety Contract

Maintain:

```text
LIVE_TRADING=false
```

throughout Prompt 27 development and testing.

Prompt 27 may certify a release candidate, but certification alone must never activate live trading.

Required separation:

```text
RESEARCH
   ↓
VALIDATED
   ↓
PAPER
   ↓
SHADOW
   ↓
CERTIFICATION ELIGIBLE
   ↓
CERTIFIED
   ↓
RELEASE AUTHORIZED
   ↓
LIVE ENABLEMENT
```

The last two states are deliberately separate.

No AI process may:
- certify itself
- promote itself
- authorize itself
- enable live trading
- override a safety gate
- waive a safety requirement
- change capital limits
- modify certification evidence

---

## 3. Architectural Boundary

Compose existing systems; do not fork them.

```text
P05 Research Gate
P20 Independent Validation
P21/P24 Paper + Shadow
P18 TCA / Capacity
P17 Production Data
P25 Safety Gateway
P26 Operations Control Plane
        │
        ▼
┌──────────────────────────────┐
│ P27 CERTIFICATION ENGINE     │
│                              │
│ Evidence                     │
│ Validation                   │
│ Model Risk                   │
│ Data Readiness               │
│ Execution Readiness          │
│ Reconciliation               │
│ Safety                       │
│ Operations                   │
│ Governance                   │
└──────────────┬───────────────┘
               ▼
      CERTIFICATION RECORD
               │
               ▼
      RELEASE ELIGIBILITY
               │
       explicit separation
               ▼
      RELEASE AUTHORIZATION
               │
               ▼
       P28 broker boundary
```

Prompt 27 must not import broker SDKs.

---

## 4. State Machine

Implement a strict state machine:

```text
DRAFT
  ↓
EVIDENCE_COLLECTING
  ↓
VALIDATION_PENDING
  ↓
VALIDATION_COMPLETE
  ↓
SHADOW_VERIFIED
  ↓
SAFETY_VERIFIED
  ↓
OPS_VERIFIED
  ↓
CERTIFICATION_REVIEW
  ↓
CERTIFIED
  ↓
RELEASE_ELIGIBLE
  ↓
EXPIRED / SUSPENDED / REVOKED
```

Invalid transitions must raise a typed exception.

Forbidden:

```text
DRAFT → CERTIFIED
FAILED → CERTIFIED
SUSPENDED → LIVE
EXPIRED → LIVE
REVOKED → LIVE
```

A certification must have:
- unique certification ID
- immutable specification hash
- evidence snapshot hash
- code/version identity
- dataset snapshot identity
- strategy/ensemble/model identity
- risk-policy identity
- execution-policy identity
- safety-policy identity
- operator identity
- independent validator identity
- issue/waiver records
- creation timestamp
- expiry timestamp

---

## 5. Certification Package

Create an immutable `CertificationPackage`.

It must bind:

```text
Research lineage
Data snapshot
Feature identities
Alpha identities
Model identities
Ensemble identity
Portfolio policy
Risk policy
Execution assumptions
TCA evidence
Paper evidence
Shadow evidence
Reconciliation evidence
Operational evidence
Safety evidence
Independent validation
Known limitations
NOT_TESTED register
Waivers
Approvals
Release limits
```

Hash the complete package.

Any material mutation must invalidate certification.

---

## 6. Certification Domains

Certification must evaluate independent domains.

### A. Research Integrity

Require:
- PIT integrity
- no future leakage
- frozen experiment identity
- reproducible results
- family/multiple-testing accounting
- falsification evidence
- retained failed candidates
- research lineage

### B. Statistical Validation

Require:
- OOS evidence
- walk-forward validation
- robustness
- stability
- statistical significance where appropriate
- dependence-aware inference
- model comparison
- multiple-testing controls
- degradation analysis

Do not certify from a single backtest.

### C. Data Readiness

Require evidence for:
- production source provenance
- security master
- symbol mapping
- corporate actions
- calendar
- timestamp semantics
- missing data
- stale data
- duplicate data
- survivorship
- snapshot integrity

Critical `NOT_TESTED` items block certification.

### D. Execution Readiness

Require:
- spread evidence
- slippage evidence
- impact model status
- latency model
- liquidity evidence
- capacity evidence
- residual handling
- partial-fill behavior
- execution reconciliation

Uncalibrated execution assumptions must remain explicitly labelled.

### E. Paper/Shadow Evidence

Require:
- deterministic replay
- paper reconciliation
- shadow behavior
- decision-to-target lineage
- target-to-intent lineage
- intent-to-paper-order lineage
- simulated-fill lineage
- residual visibility

Paper P&L must never be treated as proof of alpha.

### F. Risk Readiness

Evaluate:
- gross/net exposure
- factor exposure
- beta
- concentration
- turnover
- drawdown
- liquidity
- leverage
- capacity
- stress behavior

Unknown risk inputs remain unknown.

### G. Safety Readiness

Every applicable P25 safety gate must pass.

A safety failure blocks certification.

Safety cannot be waived.

### H. Operational Readiness

P26 must demonstrate:
- process health
- clock health
- disk health
- backup integrity
- restore test
- logging
- secrets handling
- recovery behavior
- fatal-state handling
- kill-switch operation

### I. Independent Validation

The validator must be logically separated from the strategy owner.

Require:
- validation record
- scope
- methodology
- findings
- unresolved issues
- reviewer identity
- approval/rejection

---

## 7. Gate Taxonomy

Every criterion must resolve to:

```text
PASS
FAIL
WARN
NOT_TESTED
WAIVED
NOT_APPLICABLE
```

Rules:

```text
SAFETY FAIL              → certification blocked
CRITICAL FAIL            → certification blocked
CRITICAL NOT_TESTED     → certification blocked
UNRESOLVED RECON BREAK  → certification blocked
SYNTHETIC PRODUCTION    → certification blocked
MISSING INDEPENDENT
VALIDATION              → certification blocked
EXPIRED CERTIFICATION   → release blocked
```

`WARN` is not equivalent to `PASS`.

---

## 8. Waiver System

Implement controlled waivers.

Every waiver requires:

```text
waiver_id
criterion_id
reason
risk_statement
authority
scope
created_at
expires_at
mitigation
```

Rules:
- safety requirements cannot be waived
- waivers expire automatically
- expired waivers invalidate certification where material
- AI cannot create or approve waivers
- waiver history is immutable

---

## 9. Restricted Release

Certification must define explicit release limits.

Examples:

```text
max_capital
max_gross_exposure
max_net_exposure
max_position
max_order_notional
max_turnover
max_participation
max_daily_loss
max_drawdown
max_open_orders
allowed_symbols
allowed_sessions
allowed_modes
```

The system must support staged promotion:

```text
RESEARCH
PAPER
SHADOW
RESTRICTED_LIVE
EXPANDED_LIVE
```

Do not implement unrestricted live trading in Prompt 27.

---

## 10. Expiry & Revocation

Certification must expire.

Trigger suspension/revocation on:
- safety failure
- operational failure
- reconciliation break
- material model drift
- material data-source change
- strategy hash change
- risk-policy change
- execution-policy change
- broker/account mismatch
- kill-switch activation
- unauthorized configuration mutation

Certification must never silently survive material changes.

---

## 11. Release Manifest

Generate an immutable `ReleaseManifest`.

Include:

```text
release_id
certification_id
software_version
git_commit
configuration_hash
research_snapshot_hash
data_snapshot_hash
model_hash
ensemble_hash
portfolio_policy_hash
risk_policy_hash
execution_policy_hash
safety_policy_hash
ops_health_hash
capital_limit
release_stage
expiry
approved_by
validator
timestamp
```

A material mismatch must block release.

---

## 12. Human Authorization

Human approval is required for release.

But human authorization cannot bypass:

```text
FAIL
critical NOT_TESTED
safety failure
reconciliation failure
expired certification
manifest mismatch
```

Use separation of duties:

```text
Researcher
Validator
Operations
Release Authority
```

Prefer different identities.

---

## 13. AI Boundary

AI outputs must be typed:

```text
AI_SUGGESTION
```

AI may:
- summarize evidence
- identify anomalies
- suggest additional tests
- explain failures

AI may not:
- certify
- approve
- waive safety
- increase capital
- enable live trading
- bypass reconciliation
- alter evidence
- alter release limits

---

## 14. Integrity Flags

Add explicit checks:

```text
certification_evidence_mutation
certification_snapshot_mismatch
certification_model_mismatch
certification_config_mismatch
certification_hash_mismatch
critical_not_tested
independent_validation_missing
safety_gate_failure
reconciliation_failure
paper_shadow_gap
synthetic_production_evidence
expired_certification
revoked_certification
waiver_expired
waiver_scope_violation
unauthorized_release
release_manifest_mismatch
human_approval_missing
separation_of_duties_violation
ai_certification_override
ai_authorization_override
capital_limit_mutation
release_policy_mutation
```

`None` must remain `NOT_TESTED`.

Direct integrity violations → `FAIL`.

---

## 15. CLI

Implement:

```text
quantlab certification list
quantlab certification inspect <id>
quantlab certification create
quantlab certification evidence
quantlab certification validate
quantlab certification review
quantlab certification approve
quantlab certification reject
quantlab certification certify
quantlab certification status
quantlab certification audit
quantlab certification expire
quantlab certification suspend
quantlab certification revoke
quantlab certification waivers
quantlab certification manifest
quantlab certification report
quantlab certification lineage
quantlab certification readiness
```

Research aliases:

```text
quantlab research certification
quantlab research readiness
quantlab research promotion
quantlab research release-gate
quantlab research certification-audit
```

Existing `quantlab validate` remains Prompt 05.

---

## 16. Desktop

Add:

**Certification & Promotion Lab**

It is a query/review interface only.

Qt must not:
- certify directly
- modify evidence
- modify ledger
- bypass state transitions
- enable live trading
- import broker SDKs

Display:

```text
Certification Status
Evidence Matrix
Gate Results
NOT_TESTED Register
Open Findings
Waivers
Independent Validation
Safety Status
Operational Status
Release Manifest
Expiry
Approval Chain
Audit Trail
```

---

## 17. Ledger & Knowledge

Write immutable ledger records using:

```text
selection_stage="certification"
```

Add:

```text
certification_id
certification_hash
release_id
release_manifest_hash
validation_id
approval_id
```

Knowledge nodes:

```text
CERTIFICATION
VALIDATION
RELEASE_MANIFEST
WAIVER
CERTIFICATION_FINDING
PROMOTION_EVENT
```

Never delete failed certification attempts.

---

## 18. Reproducibility

Identical:

```text
software
configuration
data snapshot
research snapshot
model
risk policy
execution policy
safety policy
```

must produce identical certification hashes.

Material differences must produce different identities.

---

## 19. Testing Requirements

Implement dedicated tests for:

- state machine
- certification immutability
- evidence completeness
- critical NOT_TESTED blocking
- safety blocking
- reconciliation blocking
- synthetic-production blocking
- independent validation requirement
- waiver expiry
- waiver scope
- manifest mismatch
- model/config mutation
- release expiry
- suspension/revocation
- AI override denial
- capital-limit mutation
- separation of duties
- deterministic certification hash
- audit lineage
- regression across Prompts 01–26

Required quality:

```text
ruff clean
mypy --strict clean on owned modules
pytest clean
UI offscreen smoke clean
LIVE_TRADING=false
zero broker imports
```

---

## 20. Explicit NOT_TESTED

Do not fabricate evidence for:

- real broker execution
- live market order routing
- production account reconciliation
- institutional TCA unless sourced
- official exchange fee schedules unless sourced
- official exchange calendars unless sourced
- real ADV unless sourced
- real order-book depth unless sourced
- live operational incidents

Represent unknowns explicitly.

---

## 21. Definition of Done

Prompt 27 is complete only when:

1. Certification is a strict state machine.
2. Certification evidence is immutable and hashed.
3. Critical failures block certification.
4. Critical `NOT_TESTED` blocks certification.
5. Safety failures cannot be waived.
6. Independent validation is mandatory.
7. Synthetic evidence cannot certify production.
8. Release limits are explicit.
9. Certification expires.
10. Material changes invalidate certification.
11. AI has no certification authority.
12. Human approval cannot bypass safety.
13. Release manifests are immutable.
14. No broker imports exist.
15. `LIVE_TRADING=false`.
16. Prompt 01–26 regression remains green.
17. Full audit lineage exists.

**Final principle:**

> Certification proves readiness against defined criteria. It does not create permission to trade.

---

## 22. Deliverables

Create:

```text
src/quantlab/certification/
docs/decisions/ADR-<next-unused>-live-trading-certification.md
docs/architecture/LIVE_TRADING_CERTIFICATION.md
docs/research/CERTIFICATION_PROTOCOL.md
docs/research/PROMOTION_POLICY.md
docs/research/RELEASE_GOVERNANCE.md
tests/certification/
```

Update:

```text
README
BACKLOG
LOCAL_RUN
architecture map
health registry
knowledge ingest
ledger schema
desktop navigation
```

Do not rewrite Prompts 01–26.

**Prompt 27 must end at certification/release eligibility.**
