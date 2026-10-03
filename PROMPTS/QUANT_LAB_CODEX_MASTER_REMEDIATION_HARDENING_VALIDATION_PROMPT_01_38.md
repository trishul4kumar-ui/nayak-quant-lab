# NAYAK QUANT LAB
# CODEX MASTER REMEDIATION, HARDENING & VALIDATION DIRECTIVE
## Prompts 01–38 System Audit Closure Program

**Repository:** `https://github.com/trishul4kumar-ui/nayak-quant-lab`
**Execution target:** OpenAI Codex / coding agent with repository access
**Scope:** Existing QUANT LAB implementation through Prompt 38
**Mode:** Autonomous deep technical remediation and validation
**Live trading policy:** **DO NOT ENABLE LIVE TRADING. DO NOT ADD A PRODUCTION BROKER-WRITE ADAPTER IN THIS PROGRAM.**
**Primary objective:** Convert the current Prompt 01–38 codebase from a large research/pre-production implementation into a coherent, internally reachable, persistence-safe, scientifically defensible, integration-tested pre-live platform.

---

# 0. MISSION

You are working on **NAYAK QUANT LAB**, a local-first quantitative research and controlled trading software platform for Indian markets.

The repository already contains a large architecture spanning:

```text
DATA
→ PIT INTEGRITY
→ FEATURES
→ LABELS
→ ALPHA
→ FACTORS
→ REGIMES
→ ADAPTIVE LEARNING
→ STATISTICAL LEARNING
→ ENSEMBLES
→ PORTFOLIO CONSTRUCTION
→ RESEARCH VALIDATION
→ CAPITAL ALLOCATION
→ PAPER OMS
→ MONITORING
→ TCA
→ ECONOMETRICS
→ MODEL-RISK CERTIFICATION
→ SHADOW
→ SAFETY
→ OPS
→ RELEASE
→ READ-ONLY BROKER GATEWAY
→ REAL-TIME DATA
→ REAL-TIME DECISION
→ DIGITAL TWIN
→ PRODUCTION SHADOW
→ EXECUTION AUTHORIZATION
→ RESTRICTED EXECUTION
→ LIVE OPERATIONS
```

This is **not** a request to add another feature layer.

This program is a **hardening, remediation, integration and scientific-validation freeze**.

The existing architecture must be respected unless a defect proves that a narrow change is required.

---

# 1. NON-NEGOTIABLE SYSTEM INVARIANTS

The following invariants must remain true throughout the work.

```text
DATA ≠ FEATURE
FEATURE ≠ LABEL
FEATURE ≠ FACTOR
FACTOR ≠ ALPHA
ALPHA ≠ MODEL
MODEL ≠ ADAPTIVE LEARNER
MODEL ≠ ENSEMBLE
ENSEMBLE ≠ PORTFOLIO
PORTFOLIO ≠ TARGET PORTFOLIO
TARGET PORTFOLIO ≠ ORDER INTENT
ORDER INTENT ≠ ORDER
SIMULATED FILL ≠ BROKER FILL
PAPER ≠ SHADOW
SHADOW ≠ LIVE
BROKER CONNECTED ≠ TRADING AUTHORIZED
CERTIFIED ≠ LIVE
AUTHORIZED ≠ SUBMITTED
AI ≠ AUTHORITY
OBSERVED ≠ MODELLED
MISSING ≠ ZERO
NOT_TESTED ≠ PASS
WARN ≠ PASS
FAIL ≠ PASS
```

Preserve these core policies:

- Point-in-time discipline: `available_time <= as_of`
- Next-bar research fill convention unless explicitly modeled otherwise
- No same-bar look-ahead
- Synthetic data is architecture evidence only
- Synthetic evidence can never certify live readiness
- `NOT_TESTED` must remain explicit
- Unknown liquidity must never become infinite liquidity
- Unknown factor exposure must never silently become zero
- Unknown broker state must never be silently repaired
- Ambiguous order submission must never be blindly retried
- Safety controls must fail closed
- AI may suggest; AI may not authorize execution
- Human authorization must remain explicit and hash-bound
- `LIVE_TRADING=false` by default
- `BROKER_WRITE_ENABLED=false` by default
- No production broker write path is to be added by this directive

---

# 2. CODEX OPERATING INSTRUCTIONS

Codex must work **autonomously and continuously** through the entire directive.

Do **not** stop after each phase to ask for permission.

Do **not** ask the user whether to continue.

Do **not** perform superficial placeholder work.

Do **not** mark a defect fixed merely because a new class or test stub exists.

For every task:

1. Inspect the current implementation first.
2. Trace all callers and dependencies.
3. Identify whether the defect is local or systemic.
4. Implement the smallest correct architectural repair.
5. Add or update tests.
6. Run targeted tests.
7. Run broader regression tests.
8. Update documentation only after code is correct.
9. Record any intentionally unimplemented behavior as explicit `NOT_TESTED`, `BLOCKED`, or backlog debt.
10. Never hide a failure to obtain a green suite.

If a requested behavior is already implemented correctly, prove it through inspection/tests and leave it unchanged.

---

# 3. FIRST ACTION — REPOSITORY BASELINE

Before modifying code, inspect and record:

```text
git status
git branch --show-current
git log --oneline --decorate -20
python --version
```

Then inspect:

```text
pyproject.toml
src/quantlab/__init__.py
README.md
docs/BACKLOG.md
docs/architecture/QUANT_LAB_ARCHITECTURE.md
docs/research/OPERATIONAL_READINESS.md
```

Then run the current quality baseline:

```bash
python -m pytest -q
ruff check src tests
mypy src/quantlab
```

If project commands are exposed through `make`, also run the appropriate Makefile targets.

Record:

- test count
- pass count
- fail count
- skip count
- xfail count
- Ruff state
- mypy state
- current version
- current repository status

Create:

```text
docs/audits/QUANT_LAB_PROMPT_01_38_PRE_REMEDIATION_BASELINE.md
```

This baseline must contain factual results only.

---

# 4. P0-01 — REPAIR THE PROMPT 35 → PROMPT 36 DEADLOCK

## Known defect

Inspect:

```text
src/quantlab/production_shadow/service.py
src/quantlab/production_shadow/models.py
src/quantlab/digital_twin/
src/quantlab/execution_authorization/service.py
```

The current production-shadow flow appears to make:

```text
deterministic_replay = NOT_TESTED
```

a critical blocker even when shadow evidence exists.

Prompt 36 then relies on:

```text
not run.readiness.critical_failures
```

Therefore the real:

```text
Prompt 35 production shadow
→ Prompt 36 execution authorization eligibility
```

happy path can be unreachable.

## Required repair

Design and implement an explicit deterministic replay evidence contract.

Preferred architecture:

```text
ProductionShadowRun
    +
DigitalTwinReplayEvidence
    ↓
validate:
    market snapshot hash
    decision hash
    target portfolio hash
    order-plan hash
    simulated fill hash
    cash/position state hash
    reconciliation hash
    deterministic replay hash
    ↓
PASS / FAIL / NOT_TESTED
```

Requirements:

- No fabricated replay evidence.
- Replay evidence must be hash-verifiable.
- Replay mismatch must be `FAIL`.
- Missing replay evidence must remain `NOT_TESTED`.
- If policy requires replay, `NOT_TESTED` must block readiness.
- A genuine supplied matching replay must produce `PASS`.
- Production shadow must be capable of reaching a clean readiness state when all required evidence is valid.
- Execution authorization must be capable of reaching `ELIGIBLE_FOR_HUMAN_REVIEW` through the **real service chain**, not a manually fabricated test fixture.

## Mandatory tests

Add integration tests proving:

```text
valid production market evidence
+ valid broker observation
+ valid reconciliation
+ valid real-time decision
+ valid shadow cycle
+ valid deterministic replay
+ intact safety wall
=
ProductionShadowRun without critical failures
```

Then prove:

```text
clean ProductionShadowRun
+ valid release evidence
+ matching broker account
+ current reconciliation
+ fresh audit evidence
=
AuthorizationState.ELIGIBLE_FOR_HUMAN_REVIEW
```

Also test:

- missing replay → blocked
- replay mismatch → blocked
- stale replay → blocked if freshness is required
- altered replay hash → blocked
- replay from different decision → blocked
- replay from different broker account → blocked if relevant
- synthetic-only production evidence → blocked

---

# 5. P0-02 — REPAIR THE RESEARCH PROMOTION GATE

Inspect:

```text
src/quantlab/research/gate.py
src/quantlab/research/multiple_testing.py
src/quantlab/research/statistics.py
src/quantlab/research/walkforward.py
src/quantlab/orchestration/
```

## Known defect

The current gate appears to create unconditional warning states such as:

```text
oos_evidence = WARN
multiple_testing = WARN
```

and then checks for any warning before allowing:

```text
RESEARCH_CANDIDATE
```

This can make the candidate state unreachable.

## Required behavior

The gate must distinguish:

```text
diagnostic existence
from
diagnostic failure
```

A completed valid OOS evaluation must not be forced to WARN merely because OOS evidence exists.

A completed multiple-testing evaluation must be represented by its actual result.

Create explicit semantics such as:

```text
PASS
WARN
FAIL
NOT_TESTED
```

for:

- OOS evidence
- walk-forward validation
- statistical significance
- multiple-testing correction
- cost robustness
- parameter robustness
- test-set integrity
- PIT integrity

Do not manufacture PASS.

## Promotion policy

Preserve:

```text
synthetic → never paper promotion
integrity failure → REJECT
test-set contamination → REJECT
zero-cost evidence → REJECT or blocked
```

Ensure that a genuine valid non-synthetic research package can reach:

```text
RESEARCH_CANDIDATE
```

and, if the architecture intends `PROMOTED_TO_PAPER` to occur in another layer, then:

- remove unreachable/dead enum logic, or
- document the exact owning layer.

Do not leave a misleading enum state that can never occur.

## Mandatory tests

Add:

- clean real-data-like fixture → candidate
- synthetic fixture → WARN only
- integrity failure → REJECT
- contaminated test set → REJECT
- valid BH/Holm/Bonferroni outcome → correct gate semantics
- multiple-testing NOT_TESTED where required → no silent promotion
- parameter fragility → WARN
- valid robust test → PASS
- no unconditional warning preventing candidate state

---

# 6. P0-03 — FIX LABEL AVAILABILITY AND TARGET IDENTITY

Inspect:

```text
src/quantlab/labels/
src/quantlab/learning/dataset.py
src/quantlab/learning/walkforward.py
src/quantlab/adaptive/
src/quantlab/ensemble/
```

## Problem A — label availability metadata is lost

`LabelObservation` contains availability information, but panelized labels may collapse to:

```text
decision_time → security_id → value
```

without preserving:

```text
label_available_time
```

A model must not train on a label merely because its decision date precedes T.

It may train only if:

```text
label_available_time <= training_cutoff
```

## Required repair

Introduce a PIT-safe label structure or companion availability panel.

Do not break existing public interfaces unnecessarily.

Acceptable patterns include:

```text
LabelPanelValue {
    value
    decision_time
    end_time
    available_time
    label_id
}
```

or:

```text
values panel
+
availability panel
```

Ensure training-row assembly filters by true label availability.

This must work for:

- 1-session labels
- multi-session labels
- delayed labels
- irregular calendars
- revised/delayed data
- future extension to fundamentals

## Problem B — declared target can disagree with generated target

Inspect `learning/dataset.py`.

If code always generates `forward_return(1)` but metadata stores `model.target`, repair it.

Required architecture:

```text
model.target
    ↓
Label registry
    ↓
resolved LabelDefinition
    ↓
computed label panel
    ↓
label definition hash/version recorded in dataset
```

A dataset must never claim one target while training on another.

## Mandatory tests

- target `forward_return_1` resolves correctly
- multi-horizon target resolves correctly
- metadata matches generated target
- labels unavailable at training cutoff are excluded
- delayed labels are excluded until available
- no future label enters training matrix
- model walk-forward remains prequential

---

# 7. P0-04 — ENSEMBLE LEAKAGE MUST NEVER PASS

Inspect:

```text
src/quantlab/ensemble/engine.py
src/quantlab/ensemble/definition.py
src/quantlab/ensemble/stacking.py
src/quantlab/ensemble/weighting.py
```

## Known defect

The engine recognizes many leakage flags but may only force FAIL for a subset.

Any intentional future-information flag must prevent a PASS research result.

Use a single authoritative leakage predicate.

Conceptually:

```python
if _leaky(flags):
    status = CheckResult.FAIL
```

with precise diagnostics identifying which leakage occurred.

Leakage modes include but are not limited to:

```text
future_weights
future_correlation
future_component_performance
future_normalization
future_meta_feature
future_component_selection
future_stacking
future_pruning
future_hyperparameter
holdout_contaminated
stacking_leak
full_sample_replay
future_covariance
future_regime
```

## Mandatory tests

Parameterize every leakage flag.

Each leakage flag individually must cause:

```text
status = FAIL
```

unless the flag is explicitly documented as a diagnostic mode whose result can never enter promotion.

No leaky result may be promoted.

---

# 8. P0-05 — RESTRICTED EXECUTION MUST ENFORCE AUTHORIZED RISK SCOPE

Inspect:

```text
src/quantlab/execution_authorization/models.py
src/quantlab/execution_authorization/service.py
src/quantlab/restricted_execution/models.py
src/quantlab/restricted_execution/service.py
src/quantlab/reconciliation/
src/quantlab/broker_gateway/
src/quantlab/safety/
```

## Current risk

Authorization scope includes values such as:

```text
max_gross_exposure
max_notional
max_turnover
```

but the restricted execution validator must prove they are enforced before submission.

## Required behavior

Before a future production adapter could ever submit:

- approval must be current
- approval must match exact scope hash
- assessment hash must match
- account fingerprint must match
- security must be authorized
- session must be valid
- intent must not be expired
- confirmation must be current
- global kill switch must be inactive
- action kill scope must be inactive
- current market-data health must be acceptable
- current broker snapshot must be fresh
- current reconciliation must be acceptable
- release/certification must remain valid
- authorization evidence must remain fresh
- order notional must respect scope
- resulting gross exposure must respect scope
- resulting turnover must respect scope
- cash/margin constraints must be known and respected
- unknown required state must fail closed

No normalization or hidden modification of the user's approved order intent.

If current market price is required for market-order notional validation and is unavailable:

```text
BLOCK
```

Do not guess.

## Critical race rule

Revalidation must occur as close as possible to the submission boundary.

An approval that was valid five minutes ago is not enough if:

```text
market data became stale
reconciliation broke
kill switch activated
account changed
release was suspended
```

## Mandatory tests

Test all of the above, including:

- limit-order notional breach
- market-order notional unknown
- gross exposure breach
- turnover breach
- stale reconciliation
- stale broker snapshot
- kill activated after confirmation
- release invalidated after confirmation
- market feed stale after confirmation
- approval expires after confirmation
- concurrent duplicate submission
- submission already attempted
- ambiguous timeout
- no retry after ambiguous timeout

---

# 9. P0-06 — DURABLE STATE FOR CONTROL-PLANE DATA

Inspect repositories including:

```text
src/quantlab/execution_authorization/repository.py
src/quantlab/restricted_execution/repository.py
src/quantlab/reconciliation/repository.py
src/quantlab/production_shadow/repository.py
src/quantlab/live_ops/repository.py
```

The current in-memory dictionaries are acceptable for tests/research but not for pre-live control-plane durability.

## Required architecture

Add a durable repository implementation using an existing project-approved local database strategy.

Preferred local-first choice:

```text
SQLite in WAL mode
```

unless the repository already has a clearly established operational database abstraction.

Do not add Postgres merely for style if it creates unnecessary deployment complexity.

However, repository interfaces must be designed so a future Postgres implementation is possible.

Critical state to persist:

```text
authorization assessments
human approvals
revocations
execution envelopes
human confirmations
submission attempts
ambiguous submission state
reconciliation reports
reconciliation exceptions
production-shadow runs
incidents
incident events
response actions
audit records
```

## Required properties

- ACID transaction boundaries
- deterministic IDs
- unique idempotency constraints
- append-only audit events
- immutable evidence payloads
- schema version
- migration mechanism
- crash/restart recovery
- no credential persistence in plaintext
- no live broker secrets in database
- safe concurrent access
- repository interfaces remain testable

Provide in-memory repository only as explicit test implementation.

## Crash-safety tests

Simulate:

```text
persist intent
→ crash
→ restart
→ recover state
```

and:

```text
record submission attempt
→ crash before broker response handling
→ restart
→ state remains SUBMISSION_UNKNOWN or equivalent
→ system must reconcile, never retry blindly
```

---

# 10. P0-07 — REMOVE ASSERTIONS FROM SAFETY BOUNDARIES

Search the entire production source tree for runtime safety behavior implemented using Python `assert`.

Examples may exist in:

```text
broker_gateway
realtime_data
realtime_decision
digital_twin
shadow
paper_oms
capital
```

Python assertions can be removed under:

```bash
python -O
```

Therefore:

```text
assert
```

must not be the only enforcement mechanism for:

```text
LIVE_TRADING=false
BROKER_WRITE_ENABLED=false
shadow-only state
release blocked
broker routing disabled
live order submission disabled
```

Replace safety assertions with explicit typed exceptions or centralized guard functions.

Keep asserts only for developer-only impossible-state diagnostics where disabling the assertion cannot weaken a safety boundary.

## Mandatory optimized-mode test

Add a CI test that runs critical safety tests with:

```bash
python -O -m pytest ...
```

Prove that safety behavior is unchanged.

---

# 11. P1-01 — BACKTEST CALENDAR AND UNIVERSE CORRECTNESS

Inspect:

```text
src/quantlab/backtest/engine.py
src/quantlab/data/fabric/calendar.py
src/quantlab/data/fabric/universe.py
src/quantlab/data/fabric/instruments.py
src/quantlab/features/engine.py
```

## Problem A — common-date intersection

Do not use the intersection of all instruments' observed dates as the canonical trading calendar for cross-sectional simulation.

The exchange/session calendar must be authoritative.

At each timestamp determine instrument eligibility separately.

Missing data for one instrument must not erase the session for every other instrument.

## Problem B — historical universe membership

All serious backtests must be capable of consuming PIT universe membership:

```text
universe.as_of(T)
```

Avoid survivorship bias.

Tests must cover:

- IPO enters after start
- delisted instrument disappears
- temporary missing bar
- suspended security
- symbol changes
- current-only constituent set not backfilled into history

## Problem C — timing contract

Formalize signal and fill timing.

For daily close-derived signals, clearly model one of:

```text
T close information
→ T+1 executable price
```

or an explicit closing-auction assumption.

Do not ambiguously use a price both as a fully known feature input and an instantly executable fill unless the execution model proves that convention.

Update `BACKTESTING_PROTOCOL.md`.

---

# 12. P1-02 — INDIA-SPECIFIC COST MODEL

The current research cost model intentionally leaves several Indian fee legs unspecified.

Preserve the research default, but build a separate versioned configurable Indian market fee schedule.

Support at least architecture for:

```text
brokerage
exchange transaction charges
STT
SEBI fees
GST
stamp duty
DP charge
```

with differences by:

```text
segment
exchange
product
side
delivery/intraday
```

Do not hard-code rates from memory.

Rates must come from user-provided/configured versioned data.

Every fee schedule must contain:

```text
effective_from
effective_to
source
version
hash
```

If fee data is missing:

```text
NOT_TESTED
```

not zero-cost certainty.

---

# 13. P1-03 — REAL MARKET-DATA PROVIDER BOUNDARY

Do **not** embed a vendor SDK into research modules.

Implement or complete the production provider contract so a real external provider can be integrated safely.

Required capabilities:

```text
connect
disconnect
heartbeat
subscribe
unsubscribe
decode
normalize
sequence validation
duplicate detection
gap detection
out-of-order detection
clock checks
staleness
reconnect
failover
coverage
source provenance
```

Keep vendor-specific code behind adapter interfaces.

If no credentials/provider are available in the development environment, provide:

- contract tests
- recorded fixture/replay tests
- explicit `NOT_CONFIGURED`
- no fake live connection

Do not claim a live feed exists unless it actually does.

---

# 14. P1-04 — LIVE OPERATIONS MUST OBSERVE REAL SYSTEM HEALTH

Inspect:

```text
src/quantlab/live_ops/
src/quantlab/ops/
src/quantlab/realtime_data/
src/quantlab/broker_gateway/
src/quantlab/reconciliation/
src/quantlab/restricted_execution/
```

Remove hardcoded operational states such as permanent:

```text
market_data = UNKNOWN
```

where real subsystem health is available.

Build typed health probes for:

```text
market data freshness
market data quality
broker connectivity
broker snapshot age
reconciliation state
authorization expiry
restricted gateway state
submission unknown count
global kill switch
database health
disk health
clock health
worker heartbeat
backup freshness
```

Where observable, also support:

```text
decision latency
snapshot latency
broker REST latency
reconciliation latency
```

No automatic resume.

Automatic containment may activate a kill switch only under an explicit configured policy.

Never auto-clear the kill switch.

---

# 15. P1-05 — TCA AND CAPACITY MUST USE REAL INPUT CONTRACTS

Inspect:

```text
src/quantlab/tca/service.py
src/quantlab/tca/calibration.py
src/quantlab/tca/capacity.py
src/quantlab/execution_research/
```

Remove hidden dependence on seed synthetic volume from production-capable code paths.

TCA requests should accept explicit, typed liquidity/execution evidence.

Keep:

```text
synthetic
modelled
observed
calibrated
stressed
```

strictly separate.

Calibration using paper fills must remain clearly labelled model-on-model or simulated calibration.

A future broker-fill calibration path must be distinct.

Capacity must never claim NSE capacity from synthetic volume.

---

# 16. P1-06 — FIX CONFIDENCE SIZING

Inspect:

```text
src/quantlab/capital/sizing.py
src/quantlab/capital/allocator.py
```

The current confidence-scaled sizing may multiply all raw scores by the same confidence scalar and then renormalize, mathematically cancelling confidence.

Repair the semantics.

Confidence should affect capital deployment/gross exposure.

A valid pattern is:

```text
base composition = normalized target weights
deployed weights = confidence_scale × base composition
cash = remaining allocation
```

Preserve constraints.

Document whether confidence controls:

```text
gross exposure
risk target
capital multiplier
or another explicit quantity
```

Do not silently alter relative ranking unless intentionally designed.

## Tests

Prove:

```text
confidence 0.9 > gross exposure at confidence 0.3
```

while composition remains identical if that is the intended rule.

---

# 17. P1-07 — BROKER SNAPSHOT CONSISTENCY WINDOW

Inspect Kite read-only adapter.

A broker snapshot assembled from multiple sequential API calls is not atomic.

Add:

```text
capture_started_at
capture_completed_at
```

or equivalent observation-window metadata.

Store per-endpoint timestamps where useful.

Reconciliation must account for this capture window.

If broker state changes inside the collection interval, do not pretend the bundle is an atomic state.

Allow policy to reject snapshots whose collection window exceeds a threshold.

---

# 18. P1-08 — CI / QUALITY GATES

Create GitHub Actions CI under:

```text
.github/workflows/
```

At minimum include:

## Static quality

```bash
ruff check src tests
mypy src/quantlab
```

## Unit/integration tests

```bash
pytest -q
```

## Safety optimized mode

```bash
python -O -m pytest <critical safety suites>
```

## Build

```bash
python -m build
```

if appropriate.

## Coverage

Generate coverage.

Do not fake a high threshold immediately if current coverage cannot support it.

Instead:

1. Measure baseline.
2. Set an enforceable threshold.
3. Document target growth.
4. Require especially high coverage for:
   - authorization
   - restricted execution
   - reconciliation
   - production shadow
   - safety
   - live ops

## Security

Add:

- secret scanning where feasible
- dependency vulnerability audit where feasible

## Branch protection documentation

Add:

```text
docs/development/CI_BRANCH_PROTECTION.md
```

describing required checks for `main`.

---

# 19. P1-09 — EXPAND LAST-MILE FAILURE TESTING

The control plane requires adversarial tests.

Add a dedicated suite such as:

```text
tests/prelive_integration/
```

Cover the end-to-end sequence:

```text
market observation
→ snapshot
→ decision
→ target portfolio
→ shadow order plan
→ simulated fills
→ account state
→ reconciliation
→ digital twin replay
→ production-shadow readiness
→ release eligibility
→ execution authorization
→ human approval
→ restricted execution validation
```

No real broker write.

Then inject failures at every boundary:

```text
stale market data
missing security mapping
broker account mismatch
unknown fill
orphan order
reconciliation mismatch
replay mismatch
scope drift
expired evidence
expired approval
kill switch
release suspension
clock drift
database unavailable
duplicate request
concurrent request
process restart
ambiguous submission
```

Every failure must have deterministic expected behavior.

---

# 20. P1-10 — THREAD/PROCESS CONCURRENCY AND IDEMPOTENCY

For submission-related components, test more than a single-process dictionary implementation.

Required properties:

```text
same idempotency key → one submission attempt
same envelope hash → one submission attempt
two processes race → one wins, one observes existing state
crash after persistence → no duplicate submission
timeout → SUBMISSION_UNKNOWN
SUBMISSION_UNKNOWN → reconcile, never blind retry
```

Use database-level uniqueness where required.

Do not rely only on Python locks for process-level correctness.

---

# 21. P1-11 — VERSION AND DOCUMENTATION GOVERNANCE

After code and tests are correct, reconcile:

```text
src/quantlab/__init__.py
pyproject.toml
README.md
docs/BACKLOG.md
docs/architecture/QUANT_LAB_ARCHITECTURE.md
docs/research/OPERATIONAL_READINESS.md
```

The repository currently contains Prompts 32–38 but may still identify itself as 3.1.0 / Prompt 01–31.

Do not bump version at the start.

Only after the full remediation suite passes, choose a coherent release version according to the repository's versioning convention.

If no convention exists, document one.

Recommended release concept:

```text
3.8.x hardening release
```

rather than inventing a new feature milestone.

README must accurately state:

```text
what exists
what is read-only
what is simulated
what is production-capable
what is NOT_CONFIGURED
what is NOT_TESTED
what cannot yet trade live
```

Never claim:

```text
production ready
profitable
live
certified
```

without supporting evidence.

---

# 22. P1-12 — SOURCE OF TRUTH FOR ARCHITECTURE

Update the architecture document to include Prompts 32–38 packages explicitly:

```text
reconciliation
production_shadow
execution_authorization
restricted_execution
live_ops
```

Document dependency direction.

Forbidden dependencies must remain explicit.

Recommended rule:

```text
research code must not import broker write boundaries
AI must not import restricted execution submit paths
production shadow must not route
authorization must not size
restricted execution must not create alpha/portfolio decisions
live ops must not create trading decisions
```

Add a static architecture test if feasible.

---

# 23. P2 — CLEANUP AND ENGINEERING DEBT

After P0/P1 issues are green:

## 23.1 Remove stale placeholder language

Examples:

```text
Phase 8
Phase 10
Prompt 01–31
future broker gateway
```

where implementation has moved beyond those descriptions.

Do not remove warnings that remain true.

## 23.2 Review duplicated concepts

Inspect whether there are multiple overlapping:

```text
reconciliation implementations
broker abstractions
order state machines
health models
```

Do not merge them blindly.

Document ownership boundaries and remove only accidental duplication.

## 23.3 Dead code

Run static inspection for:

```text
unused modules
dead enums
unreachable states
obsolete compatibility bridges
```

Do not remove public compatibility APIs unless safe.

## 23.4 Logging

Ensure:

```text
API keys
access tokens
account identifiers
authorization confirmation secrets
raw credentials
```

never appear in logs.

Hashed account fingerprints are acceptable if appropriately handled.

---

# 24. DO NOT IMPLEMENT THESE AS PART OF THIS PROGRAM

Do not add:

```text
autonomous live trading
production Kite order placement
OpenAlgo live order placement
fully automatic execution
AI execution authorization
AI incident resolution
AI kill-switch clearing
RL trader
LLM trader
new strategy zoo
new alpha zoo
new feature zoo
new prompt phase
```

Do not optimize for more features.

Optimize for correctness.

---

# 25. REQUIRED SCIENTIFIC VALIDATION RULES

No code path may imply profitability.

Maintain explicit distinction:

```text
software correctness
≠
research validity
≠
statistical significance
≠
economic significance
≠
tradability
≠
capacity
≠
profitability
```

All research reports must preserve:

```text
data_kind
dataset version
snapshot
universe version
feature versions
label version
model version
cost model version
execution model version
seed
software version
config hash
```

When real data is unavailable:

```text
NOT_TESTED
```

Do not replace missing NSE evidence with synthetic assumptions.

---

# 26. REQUIRED FINAL END-TO-END VALIDATION

When remediation is complete, run a full non-live integration exercise.

The final chain must demonstrate:

```text
PIT data
→ feature calculation
→ forward label
→ research experiment
→ walk-forward validation
→ multiple-testing accounting
→ research gate
→ target portfolio
→ capital allocation
→ paper OMS
→ shadow cycle
→ monitoring
→ TCA
→ model-risk validation
→ release eligibility
→ read-only broker snapshot fixture/real read-only if configured
→ reconciliation
→ real-time snapshot
→ real-time decision
→ digital twin replay
→ production-shadow readiness
→ execution authorization eligibility
→ human approval
→ restricted execution validation
```

Final step:

```text
STOP BEFORE PRODUCTION BROKER WRITE
```

The system must prove that `DisabledWriteAdapter` remains the production default.

---

# 27. ACCEPTANCE CRITERIA

This directive is complete only when all of the following are true.

## Architecture

- [ ] Prompt 35 → 36 happy path is reachable through real services.
- [ ] Research candidate state is reachable through a valid non-synthetic research package.
- [ ] No research gate is permanently locked by unconditional WARN logic.
- [ ] Label target identity is exact.
- [ ] Label availability is enforced.
- [ ] Ensemble leakage can never produce PASS.
- [ ] Restricted execution enforces authorized risk scope.
- [ ] Safety guards do not depend on Python `assert`.
- [ ] Critical state survives restart.
- [ ] No real broker write adapter is added.

## Research

- [ ] PIT checks remain intact.
- [ ] Dynamic universe support exists for serious backtests.
- [ ] Calendar behavior does not drop entire sessions because one instrument is missing.
- [ ] Execution timing is explicitly documented.
- [ ] Indian fee schedules are versionable and not invented.
- [ ] TCA does not silently use seed synthetic liquidity in production paths.
- [ ] Confidence scaling affects deployment as intended.

## Operations

- [ ] Authorization state is durable.
- [ ] Submission state is durable.
- [ ] Reconciliation state is durable.
- [ ] Incidents are durable.
- [ ] Idempotency survives process restart.
- [ ] Ambiguous submissions remain non-retriable without reconciliation.
- [ ] Health signals consume actual subsystem states.
- [ ] No automatic resume exists.

## Quality

- [ ] Full test suite passes.
- [ ] Ruff passes.
- [ ] mypy strict passes or all remaining exceptions are explicitly justified.
- [ ] Critical tests pass under `python -O`.
- [ ] CI exists.
- [ ] Package/build succeeds.
- [ ] README and architecture match reality.
- [ ] Version metadata is consistent.

---

# 28. REQUIRED FINAL REPORTS

Create:

```text
docs/audits/QUANT_LAB_PROMPT_01_38_REMEDIATION_REPORT.md
```

Include:

1. Baseline state
2. Every defect investigated
3. Root cause
4. Files changed
5. Architectural changes
6. Tests added
7. Tests executed
8. Final test counts
9. Ruff result
10. mypy result
11. optimized-mode safety result
12. CI result
13. Remaining NOT_TESTED items
14. Remaining blockers to live production
15. Explicit statement on whether production broker writes exist
16. Explicit statement on whether profitability has been demonstrated

Also create:

```text
docs/audits/QUANT_LAB_PROMPT_01_38_REMAINING_RISKS.md
```

Classify remaining issues:

```text
P0
P1
P2
P3
NOT_TESTED
EXTERNAL_DEPENDENCY
DATA_DEPENDENCY
BROKER_DEPENDENCY
```

---

# 29. REQUIRED FINAL CODEX RESPONSE

At completion, Codex must return a concise implementation summary containing:

```text
Repository state:
Version:
Files changed:
P0 defects fixed:
P1 defects fixed:
Tests passed:
Tests failed:
Tests skipped:
Ruff:
mypy:
python -O safety tests:
CI:
Production market feed configured:
Read-only Kite configured:
Production broker write adapter present:
LIVE_TRADING default:
BROKER_WRITE_ENABLED default:
Prompt 35→36 reachable:
Research candidate reachable:
Durable control-plane persistence:
Remaining blockers:
```

Do not say “production ready” unless every relevant requirement is actually satisfied.

Do not say “profitable” unless supported by real, out-of-sample, cost-adjusted, capacity-aware evidence.

---

# 30. FINAL DIRECTIVE

Treat this work as an institutional pre-live hardening program.

The goal is not maximum code volume.

The goal is:

```text
CORRECTNESS
→ REPRODUCIBILITY
→ SCIENTIFIC INTEGRITY
→ FAILURE SAFETY
→ DURABILITY
→ OBSERVABILITY
→ DETERMINISM
→ AUDITABILITY
```

Preserve QUANT LAB's strongest design principle:

```text
UNKNOWN MUST REMAIN UNKNOWN
UNTIL EVIDENCE MAKES IT KNOWN.
```

Complete the entire remediation sequence without pausing for permission between phases.

Stop before any real broker-write capability.
