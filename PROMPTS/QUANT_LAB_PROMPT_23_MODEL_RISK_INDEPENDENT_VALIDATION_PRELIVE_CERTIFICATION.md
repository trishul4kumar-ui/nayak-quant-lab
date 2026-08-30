# QUANT LAB PROMPT 23
## Institutional Model Risk Management, Independent Validation & Pre-Live Certification Engine
### Build on QUANT LAB 2.2.0

**Cursor directive:** Implement this on the existing QUANT LAB repository after Prompt 22. Do not reset, rewrite, fork, or duplicate prior engines. Inspect and preserve Prompts 01–22, ADRs, package boundaries, integrity semantics, knowledge graph, ledger, `quantlab.app`, UI, paper OMS, TCA, monitoring, production data, econometrics, and global live-safety controls.

## Mission

Build an institutional-grade **Model Risk Management, Independent Validation & Pre-Live Certification Engine** answering:

> Is a research strategy/model sufficiently evidenced, reproducible, robust, executable, operationally controlled, and independently validated to progress to the next controlled stage?

Certification is governance, not broker permission.

## Fundamental separation

```text
RESEARCH RESULT ≠ VALIDATED MODEL
≠ APPROVED STRATEGY ≠ DEPLOYABLE STRATEGY
≠ LIVE ORDER AUTHORITY
```

Do not activate live trading.

## Architecture

Create a thin validation/certification package using existing engines:

```text
Prompt 04 data/PIT
05 gate
06 alpha/features
08 risk
09 regimes
10 adaptive
11 learning
12 ensemble
13 execution research
14 orchestration
15 discovery
16 knowledge
17 capital
18 paper OMS
19 monitoring
20 production data
21 TCA/capacity
22 econometrics
```

Do not create another backtester, PIT fabric, risk engine, TCA engine, OMS, FDR engine, or ledger.

## Candidate identity

Create immutable candidate/version identity referencing:

```text
candidate
strategy
model
alpha/ensemble
portfolio policy
capital policy
risk policy
paper OMS policy
dataset snapshot
feature/factor versions
regime definition
execution/TCA policy
econometric specifications
experiment family
knowledge lineage
software version/commit
configuration hash
```

Material changes require a new version.

## Independent validation

Represent logical roles:

```text
RESEARCHER
VALIDATOR
RISK_REVIEWER
DATA_REVIEWER
EXECUTION_REVIEWER
OPERATIONS_REVIEWER
CERTIFICATION_REVIEWER
```

A single-user installation may use logical roles, but role separation and audit history must remain explicit.

## Validation domains

Assess independently:

### Data
PIT, provenance, snapshots, corporate actions, universe history, survivorship, calendar, missing data, restatements, reconciliation.

### Research
Preregristration, lineage, search degrees of freedom, candidate count, multiple testing, falsification, replication, ablation, sensitivity, OOS and walk-forward evidence.

### Statistics
Prompt 05 + Prompt 22: effect size, confidence intervals, HAC/dependence, stationarity, structural stability, residual diagnostics, multiple testing, economic significance.

### Stability
Time windows, regimes, parameters, features, universe, costs, execution, capital, seeds, leave-one-out and ablation.

### Execution
Prompt 13/21: spread, slippage, impact, latency, partial fills, liquidity, capacity, turnover and net edge.

### Risk/capital
Prompt 08/17: concentration, factor exposures, leverage, drawdown, volatility, turnover, risk budgets and stress scenarios.

### Paper
Prompt 18: lifecycle, simulated fills, cash/position reconciliation, hashes, TCA and implementation evidence.

### Monitoring
Prompt 19: P&L, drift, risk, execution, data health, signal decay, regime/model anomalies and escalation.

### Production readiness
Prompt 20: provenance, calendar, security master, corporate actions, universe, quality, source reconciliation and coverage.

### Operations
Startup health, persistence, recovery, idempotency, duplicate prevention, clock/timezone, stale data, session handling, logging, exceptions.

### Safety
HALT, EMERGENCY, stale/invalid data, reconciliation breaks, unexpected position/cash, execution anomalies, drawdown and connectivity failures.

## Model risk taxonomy

Create `ModelRiskAssessment` with:

```text
conceptual
data
implementation
parameter
estimation
overfitting
regime
liquidity
execution
operational
software
dependency
monitoring
governance
```

Severity:

```text
LOW
MEDIUM
HIGH
CRITICAL
NOT_ASSESSED
```

No hidden defaults.

## Benchmark hierarchy

Require suitable baselines such as:

```text
no_signal
equal_weight
simple momentum/reversal
best simple component
risk-only baseline
random/sign-flip null
```

Complexity must demonstrate incremental information.

## Certification checklist

Create immutable checklist items:

```text
DATA_PIT
DATA_PROVENANCE
DATA_CORPORATE_ACTIONS
SURVIVORSHIP
RESEARCH_LINEAGE
MULTIPLE_TESTING
OOS_VALIDATION
STATISTICAL_VALIDATION
REGIME_STABILITY
EXECUTION_VALIDATION
TCA
CAPACITY
RISK
CAPITAL
PAPER_RECONCILIATION
MONITORING
OPERATIONAL_READINESS
SAFETY
AI_GOVERNANCE
```

States:

```text
PASS FAIL WARN NOT_TESTED WAIVED
```

WAIVED requires waiver ID, reason, authority, timestamp, scope and expiry.

## State machine

Implement strict transitions:

```text
DRAFT
→ UNDER_VALIDATION
→ VALIDATION_FAILED
→ VALIDATION_PASSED
→ PAPER_ELIGIBLE
→ PAPER_ACTIVE
→ PAPER_FAILED
→ SHADOW_ELIGIBLE
→ SHADOW_ACTIVE
→ PRELIVE_REVIEW
→ CERTIFIED
→ SUSPENDED
→ RETIRED
```

Illegal transitions raise typed exceptions.

Never allow `DRAFT → CERTIFIED` or `RESEARCH → LIVE`.

## Certification rules

Default conservative policy:

```text
FAIL → BLOCK
critical NOT_TESTED → BLOCK
unresolved reconciliation → BLOCK
synthetic production evidence → BLOCK
safety failure → BLOCK
```

WARN may permit continued research, not automatic certification.

Never reduce certification to a single Sharpe/CAGR/IC score.

## Reproduction

Implement:

```text
validation_replay
spec_reconstruction
snapshot_reconstruction
result_hash_comparison
environment_check
```

Any unexplained reproduction difference produces `REPRODUCTION_BREAK` and blocks certification.

## Change management

Classify:

```text
MINOR
MATERIAL
MAJOR
```

Material changes include feature formulas, universe, alpha expression, model architecture, hyperparameters, training, regimes, constraints, execution assumptions, capital policy and risk limits. Material changes require revalidation.

## Suspension/retirement

Support suspension for:

```text
performance decay
data failure
risk breach
execution deterioration
capacity collapse
regime incompatibility
reconciliation break
software defect
model drift
validation expiry
```

Retired models remain immutable in Knowledge Lab.

## AI governance

AI may assist research, but cannot:

```text
override risk
override certification
override reconciliation
override safety
change capital limits
modify gates
request live orders
```

## CLI

Add:

```text
quantlab validation list
quantlab validation inspect <candidate>
quantlab validation create <candidate>
quantlab validation checklist <candidate>
quantlab validation run <candidate>
quantlab validation reproduce <candidate>
quantlab validation risk <candidate>
quantlab validation stability <candidate>
quantlab validation economics <candidate>
quantlab validation execution <candidate>
quantlab validation paper <candidate>
quantlab validation operations <candidate>
quantlab validation safety <candidate>
quantlab validation certify <candidate>
quantlab validation suspend <candidate>
quantlab validation retire <candidate>
quantlab validation report <candidate>
quantlab validation lineage <candidate>
quantlab validation diff <a> <b>
```

Aliases:

```text
quantlab research model-risk
quantlab research validation
quantlab research certification
quantlab research reproducibility
quantlab research readiness
quantlab research governance
```

## Desktop

Add **Validation & Certification Lab** via `quantlab.app`.

Qt is viewer-only and cannot force certification or live mode.

Display candidate, state, data, research, statistics, execution, TCA, capacity, risk, paper, monitoring, operations, safety, findings, waivers, reproduction and certification.

## Global live boundary

At completion:

```text
LIVE_TRADING=false
```

No Zerodha/Kite/OpenAlgo activation or broker imports.

Prompt 23 ends at controlled pre-live certification. The future broker gateway requires a separate program.

## Auditability

Every certification must hash and retain:

```text
certification_id
candidate_id
checklist_hash
evidence_hash
snapshot_hash
spec_hash
validation_hash
knowledge_snapshot
software_version
timestamp
validator_role
open_findings
waivers
expiry
```

## Testing

Create meaningful tests for state transitions, blocking, NOT_TESTED handling, waivers, reproduction, version mismatch, paper reconciliation, TCA/capacity, risk, monitoring, safety, AI denial, synthetic blocking, lineage, determinism, suspension, retirement and UI smoke.

Target **≥100 dedicated validation/certification tests** plus full regression.

## Documentation

Create:

```text
docs/architecture/MODEL_RISK_MANAGEMENT.md
docs/architecture/VALIDATION_CERTIFICATION_ENGINE.md
docs/research/MODEL_VALIDATION_PROTOCOL.md
docs/research/INDEPENDENT_VALIDATION.md
docs/research/MODEL_RISK.md
docs/research/PRELIVE_CERTIFICATION.md
docs/research/REPRODUCIBILITY.md
docs/research/MODEL_CHANGE_MANAGEMENT.md
docs/research/MODEL_RETIREMENT.md
docs/decisions/ADR-037-model-risk-validation-certification.md
```

Update README, BACKLOG, LOCAL_RUN, architecture map, health and version.

## Definition of done

```text
__version__ = 2.3.0
ruff clean on owned code
mypy --strict clean on owned code
≥100 dedicated validation tests
full regression passes
UI offscreen smoke passes
LIVE_TRADING=false
zero live broker imports
state machine enforced
critical NOT_TESTED blocks certification
synthetic production evidence blocks certification
reproduction works
knowledge lineage works
paper reconciliation integrated
TCA/capacity integrated
risk integrated
monitoring integrated
AI cannot override certification
```

**Institutional principle:** the purpose is not to make QUANT LAB trade sooner. It is to make the system earn the right to progress. Prefer `ABSTAIN` over false confidence and `REJECT` over unvalidated deployment.
