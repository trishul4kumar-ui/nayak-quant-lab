# QUANT LAB — CURSOR IMPLEMENTATION PROMPT 14
## Advanced Research Orchestration, Experiment Management & Scientific Discovery Engine

**Target Version:** QUANT LAB 1.4.0  
**Current Baseline:** QUANT LAB 1.3.0  
**Prompt:** 14  
**Status:** IMPLEMENTATION SPECIFICATION  
**Primary Objective:** Build a research-control plane that orchestrates the existing PIT data, feature, alpha, portfolio, risk, adaptive-learning, statistical-learning, ensemble, validation, execution-research, integrity, gate, and experiment-ledger systems into one reproducible scientific discovery workflow.

---

# 0. EXECUTIVE DIRECTIVE

You are modifying an existing quantitative research laboratory.

**Do not rewrite QUANT LAB.**

**Do not create a second data fabric.**

**Do not create a second backtester.**

**Do not create a second portfolio optimizer.**

**Do not create a second covariance engine.**

**Do not create a second validation gate.**

**Do not create a parallel experiment ledger.**

Build **Prompt 14 on top of the existing QUANT LAB 1.3.0 architecture**.

The purpose of this prompt is to create the **Research Control Plane**: a scientific orchestration layer capable of defining hypotheses, constructing reproducible experiments, recording the complete research lineage, coordinating existing research engines, controlling multiple testing, comparing competing hypotheses, executing research grids, detecting researcher degrees of freedom, and producing auditable discovery reports.

The system must answer:

> **What hypothesis was tested, using exactly what information, under what PIT constraints, with what models and alternatives, how many experiments were attempted, what was discovered, what failed, and does the result survive appropriate validation and multiple-testing controls?**

QUANT LAB must behave like a **quantitative research laboratory**, not an automated stock-picking chatbot.

---

# 1. NON-NEGOTIABLE ARCHITECTURAL INVARIANTS

All existing invariants remain authoritative.

## 1.1 Single canonical components

Use exactly:

- Existing PIT Data Fabric
- Existing `MarketState`
- Existing Feature Engine
- Existing Label Engine
- Existing Alpha Engine
- Existing Portfolio Construction
- Existing Risk / Factor Engine
- Existing Regime Engine
- Existing Adaptive Engine
- Existing Statistical Learning Engine
- Existing Ensemble Engine
- Existing `run_backtest`
- Existing Execution Research Engine
- Existing Prompt 05 Research Gate
- Existing Experiment Ledger
- Existing integrity framework

The orchestration engine coordinates these systems. It does not replace them.

---

# 2. SCIENTIFIC PRINCIPLES

Implement the following principles as architectural rules.

## 2.1 Hypothesis before experiment

Every substantive research experiment must have:

- hypothesis
- null hypothesis where applicable
- economic rationale
- expected direction
- target variable
- information timestamp
- evaluation horizon
- universe definition
- feature/alpha/model specification
- validation protocol
- stopping / selection policy
- provenance

Do not allow an opaque "try everything and select the best Sharpe" workflow.

---

## 2.2 Research is sequential

Represent research as:

```text
HYPOTHESIS
    ↓
DESIGN
    ↓
DATA SNAPSHOT
    ↓
FEATURES / ALPHA
    ↓
MODEL
    ↓
PORTFOLIO
    ↓
RISK
    ↓
EXECUTION
    ↓
VALIDATION
    ↓
STATISTICAL INFERENCE
    ↓
MULTIPLE-TEST CONTROL
    ↓
RESEARCH GATE
    ↓
LEDGER
```

---

## 2.3 Discovery is not confirmation

The system must distinguish:

```text
DISCOVERY
CONFIRMATION
REPLICATION
VALIDATION
PROMOTION
```

A discovery may generate a promising hypothesis.

It must not automatically become a validated strategy.

---

# 3. CRITICAL CONCEPTUAL SEPARATION

Maintain these boundaries:

```text
DATA
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
ORDER INTENT
≠
EXECUTION
≠
RESEARCH EXPERIMENT
≠
RESEARCH HYPOTHESIS
```

A research experiment is an orchestration object. It is not an alpha, model, portfolio, or backtest.

---

# 4. NEW PACKAGE

Create:

```text
src/quantlab/orchestration/
```

Keep `__init__.py` deliberately thin.

Do not introduce circular imports.

Recommended modules:

```text
quantlab/orchestration/
├── __init__.py
├── contracts.py
├── hypothesis.py
├── experiment.py
├── specification.py
├── registry.py
├── orchestrator.py
├── planner.py
├── runner.py
├── lineage.py
├── provenance.py
├── snapshot.py
├── comparison.py
├── discovery.py
├── replication.py
├── multiple_testing.py
├── selection.py
├── stopping.py
├── search_space.py
├── research_grid.py
├── sensitivity.py
├── ablation.py
├── falsification.py
├── robustness.py
├── family.py
├── budget.py
├── scheduler.py
├── report.py
├── status.py
└── errors.py
```

Adapt naming to the existing repository conventions where appropriate.

---

# 5. CORE DOMAIN OBJECTS

Implement immutable, versioned research objects.

## 5.1 Hypothesis

A hypothesis must contain at minimum:

```text
hypothesis_id
version
title
description
economic_rationale
null_hypothesis
expected_direction
target
horizon
universe_definition
information_cutoff
status
created_at
parent_hypothesis
tags
provenance
identity_hash
```

Example:

```text
H-MOM-001

Hypothesis:
Medium-term relative strength contains incremental information
about next-period cross-sectional returns.

Expected direction:
positive

Null:
Conditional expected return has no cross-sectional relationship
with the feature after costs and controls.
```

Do not hard-code this hypothesis into the engine.

---

# 6. EXPERIMENT OBJECT

Create a versioned `ResearchExperiment`.

Required fields:

```text
experiment_id
experiment_version
hypothesis_id
dataset_id
dataset_snapshot
universe_id
feature_set
label_definition
alpha_definition
model_definition
ensemble_definition
portfolio_definition
risk_definition
execution_definition
validation_definition
multiple_testing_family
random_seed
compute_budget
created_at
started_at
completed_at
status
parent_experiment
identity_hash
config_hash
```

The complete experiment configuration must be hashable.

Changing any research-defining parameter must produce a new identity.

Never overwrite an existing experiment.

---

# 7. EXPERIMENT REGISTRY

Build a persistent registry.

It must answer:

```text
What was tested?
When?
Against which data snapshot?
With which code/configuration?
Under which hypothesis?
Which alternatives were tested?
What was the result?
Was it discovery or confirmation?
Did it pass integrity?
What gate outcome was produced?
```

Registry records must be immutable after finalization except through explicit superseding/versioning.

---

# 8. RESEARCH LINEAGE

Every result must have a lineage graph.

Example:

```text
Dataset Snapshot
       │
       ▼
Universe
       │
       ▼
Feature Definition
       │
       ▼
Alpha Definition
       │
       ├──────────────┐
       ▼              ▼
Model A           Model B
       │              │
       └──────┬───────┘
              ▼
          Ensemble
              │
              ▼
          Portfolio
              │
              ▼
             Risk
              │
              ▼
        Execution Model
              │
              ▼
         Backtest Result
              │
              ▼
       Validation Result
              │
              ▼
      Multiple-Test Result
              │
              ▼
       Research Gate
```

Persist parent-child relationships.

No result should exist without traceable ancestry.

---

# 9. DATA SNAPSHOT CONTROL

An experiment must reference a specific PIT dataset snapshot.

Store:

```text
dataset_id
dataset_version
snapshot_checksum
catalog_identity
coverage_start
coverage_end
available_at_policy
universe_identity
corporate_action_policy
calendar_identity
```

Never silently rerun an old experiment against newer data.

A new dataset snapshot creates a new research lineage.

---

# 10. EXPERIMENT TYPES

Support explicit experiment classes.

Minimum:

```text
DISCOVERY
CONFIRMATION
REPLICATION
ROBUSTNESS
ABLATION
FALSIFICATION
SENSITIVITY
MODEL_COMPARISON
ENSEMBLE_COMPARISON
PORTFOLIO_COMPARISON
EXECUTION_COMPARISON
REGIME_CONDITIONAL
TEMPORAL_STABILITY
```

Each type should have an explicit contract.

---

# 11. RESEARCH WORKFLOW

Implement:

```text
define hypothesis
        ↓
freeze specification
        ↓
resolve PIT dataset
        ↓
validate research inputs
        ↓
construct research plan
        ↓
execute candidate experiment
        ↓
record result
        ↓
run robustness / falsification
        ↓
apply multiple-testing procedure
        ↓
compare against baselines
        ↓
run research gate
        ↓
write immutable ledger record
```

The orchestrator must never bypass existing safety or integrity gates.

---

# 12. BASELINE-FIRST DESIGN

Every model/alpha discovery experiment should support a baseline.

Examples:

```text
no_signal
mean_baseline
existing_alpha
simple_linear_model
equal_weight
static_portfolio
existing_best_candidate
```

A complex model must demonstrate incremental value relative to a simpler baseline.

Do not reward complexity merely for producing higher in-sample performance.

---

# 13. ABLATION ENGINE

Implement ablation testing.

Questions:

```text
Does the alpha work without feature X?
Does the model work without regime information?
Does the ensemble work without component A?
Does the portfolio work without leverage?
Does the edge survive realistic costs?
Does execution destroy the apparent edge?
```

Record:

```text
full_model
ablated_component
delta_metric
statistical_effect
economic_effect
gate_outcome
```

---

# 14. FALSIFICATION ENGINE

This is mandatory.

The research engine must actively try to disprove a hypothesis.

Support tests such as:

```text
sign reversal
time permutation where statistically valid
cross-sectional permutation
feature destruction
label destruction
placebo feature
placebo period
regime placebo
cost stress
slippage stress
execution stress
universe perturbation
parameter perturbation
```

Do not call IID permutation automatically valid for financial time series.

Reuse the appropriate block/bootstrap/null methods from Prompt 05.

A failed hypothesis is a valid scientific result.

---

# 15. RESEARCH SEARCH SPACE

Implement an explicit `SearchSpace`.

Example:

```text
momentum_window:
    [5, 10, 20, 40, 60]

vol_window:
    [10, 20, 60]

portfolio_size:
    [5, 10, 20]

weighting:
    [equal, rank, zscore]

cost:
    [10bps, 20bps, 30bps]

execution:
    [base, conservative, stressed]
```

Every candidate generated from this space must be recorded.

Never hide candidate generation.

---

# 16. MULTIPLE-TESTING CONTROL

This is one of the most important components.

Track the number and identity of hypotheses tested.

Implement family-level research accounting.

At minimum support:

```text
Bonferroni
Holm
Benjamini-Hochberg
```

Reuse existing Prompt 05 statistical infrastructure where possible.

Do not claim that correcting p-values alone solves data mining.

Track:

```text
family_id
family_definition
hypothesis_count
tested_count
selected_count
correction_method
adjusted_p_value
selection_policy
```

---

# 17. RESEARCH FAMILY

Create:

```text
ResearchFamily
```

A family represents hypotheses sharing a common research question.

Example:

```text
Family:
"Does price momentum predict next-month cross-sectional returns?"

Candidates:
momentum_5
momentum_10
momentum_20
momentum_40
momentum_60
```

All candidate tests must remain visible.

The system must not only store the winner.

---

# 18. RESEARCHER DEGREES OF FREEDOM

Track potentially influential choices.

Examples:

```text
feature selection
lookback selection
universe selection
label horizon
cost assumption
portfolio size
rebalance frequency
model selection
hyperparameters
regime definition
execution assumptions
outlier treatment
missing-data treatment
normalization
winsorization
```

Produce a:

```text
research_degrees_of_freedom_report
```

This is diagnostic, not a magical statistical correction.

---

# 19. STOPPING RULES

Do not allow:

```text
run experiments forever
select best result
stop when Sharpe looks good
```

Support explicit stopping policies:

```text
fixed_budget
fixed_candidate_count
pre_registered_search_space
time_budget
manual_stop
```

Record the stopping policy.

A post-hoc stopping rule must be flagged.

---

# 20. RESEARCH BUDGET

Implement experiment budgets.

Budget dimensions:

```text
max_candidates
max_model_fits
max_feature_combinations
max_runtime
max_random_seeds
max_backtests
```

The orchestrator must fail clearly when the budget is exceeded.

Do not silently continue.

---

# 21. RESEARCH GRID EXECUTION

Implement a controlled research grid.

Example:

```text
Hypothesis
   │
   ├── Feature A
   │     ├── Model 1
   │     ├── Model 2
   │     └── Model 3
   │
   ├── Feature B
   │     ├── Model 1
   │     ├── Model 2
   │     └── Model 3
   │
   └── Feature C
         ├── Model 1
         ├── Model 2
         └── Model 3
```

Each node must be independently identifiable.

No anonymous experiments.

---

# 22. PARALLELISM SAFETY

If parallel execution is implemented:

- preserve deterministic identities
- preserve experiment ordering in the ledger
- isolate mutable model state
- never share adaptive state across experiments unless explicitly specified
- never share mutable caches that can alter results
- preserve random seeds
- ensure failures are recorded
- never allow one experiment to modify another experiment's configuration

Parallel execution must not change scientific results.

---

# 23. REPLICATION ENGINE

Implement replication.

A replication must distinguish:

```text
same dataset
new random seed
new time period
new PIT snapshot
new universe
new market regime
```

A result replicated only on the same synthetic slice is not external validation.

Record replication strength explicitly.

---

# 24. TEMPORAL REPLICATION

Support:

```text
train period
validation period
holdout period
replication period
```

Reuse Prompt 05 walk-forward / purge / embargo machinery.

Do not create another walk-forward implementation.

---

# 25. CROSS-SECTIONAL REPLICATION

Allow research to test whether a relationship survives across:

```text
sub-universes
time periods
sectors when PIT sector data exists
market-cap buckets when PIT cap data exists
volatility states
regimes
liquidity buckets
```

If required data is unavailable:

```text
NOT_TESTED
```

Never fabricate missing dimensions.

---

# 26. SENSITIVITY MATRIX

Implement a research sensitivity matrix.

Example:

| Dimension | Base | Conservative | Stress |
|---|---|---|---|
| Costs | 10 bps | 20 bps | 30 bps |
| Slippage | Base | High | Extreme |
| Lookback | 20 | 10/40 | 5/60 |
| Portfolio size | 10 | 5/20 | 3/30 |
| Execution | Base | Partial | High impact |

Produce:

```text
metric
median
mean
min
max
dispersion
failure_rate
gate_distribution
```

Do not collapse sensitivity into one optimistic number.

---

# 27. DISCOVERY SCORECARD

Create a research scorecard.

Suggested fields:

```text
economic_rationale
statistical_strength
out_of_sample_strength
temporal_stability
cross_sectional_stability
execution_survival
cost_survival
risk_adjusted_quality
complexity_penalty
multiple_testing_adjustment
falsification_result
replication_result
data_quality
integrity_status
gate_outcome
```

This is a research diagnostic.

It must not become a hidden proprietary "magic score."

---

# 28. COMPLEXITY PENALTY

Track model complexity.

Examples:

```text
feature_count
parameter_count
model_depth
ensemble_component_count
hyperparameter_count
research_choices
```

Report complexity alongside performance.

Do not automatically subtract arbitrary performance points unless explicitly configured.

---

# 29. RESEARCH COMPARISON

Implement statistically responsible comparisons.

Compare:

```text
candidate A
candidate B
baseline
null
best known candidate
```

Metrics may include:

```text
IC
rank IC
return
volatility
Sharpe
Sortino
max drawdown
turnover
cost drag
execution drag
capacity
stability
```

Reuse canonical calculations.

---

# 30. SELECTION POLICY

The selection engine must support explicit policies:

```text
best_oos_metric
best_risk_adjusted_metric
minimum_complexity
robustness_first
execution_survival
pareto_frontier
manual_selection
```

Selection must record the policy used.

Do not silently select the maximum Sharpe.

---

# 31. PARETO ANALYSIS

Support multi-objective research.

Potential objectives:

```text
maximize expected edge
maximize stability
maximize execution survival
minimize turnover
minimize drawdown
minimize complexity
minimize cost sensitivity
```

Return Pareto candidates rather than forcing one winner.

---

# 32. DISCOVERY VS PROMOTION

Hard rule:

```text
Discovery ≠ Promotion
```

The orchestration engine may produce:

```text
DISCOVERED
PROMISING
ROBUST_CANDIDATE
REPLICATED
```

But the final promotion state must continue to come from the existing Prompt 05 research gate.

The orchestrator cannot override it.

---

# 33. SYNTHETIC DATA RULE

Synthetic data must never become evidence of real market alpha.

Synthetic experiments may validate:

- software correctness
- deterministic behavior
- lineage
- integrity
- orchestration
- expected failure behavior

Synthetic results remain constrained to:

```text
WARN
```

and cannot become:

```text
RESEARCH_CANDIDATE
PROMOTED_TO_PAPER
LIVE
```

---

# 34. INTEGRITY CHECKS

Add explicit integrity checks.

At minimum:

```text
experiment_identity_mutation
experiment_config_mutation
future_experiment_selection
future_candidate_selection
future_hypothesis_selection
hidden_candidate
hidden_failed_experiment
hidden_search
posthoc_stopping
multiple_testing_omission
family_definition_mutation
research_budget_bypass
replication_contamination
holdout_reuse
future_baseline_selection
future_model_selection
future_execution_selection
future_cost_selection
lineage_break
dataset_snapshot_mismatch
result_overwrite
parallel_state_leak
adaptive_state_cross_contamination
```

Semantics:

```text
proven leak → FAIL
not evaluated → NOT_TESTED
verified clean → PASS
```

Never convert `NOT_TESTED` to `PASS` merely because no failure was observed.

---

# 35. LEDGER INTEGRATION

Do not create a second ledger.

Extend the existing Experiment Ledger with orchestration metadata where compatible.

Every completed experiment should record:

```text
experiment_id
hypothesis_id
family_id
dataset_snapshot
config_hash
candidate_identity
parent_experiment
research_type
search_space
candidate_count
tested_count
selection_policy
stopping_policy
multiple_testing_method
baseline
validation_result
robustness_result
falsification_result
execution_result
gate_result
integrity_result
lineage
```

---

# 36. REPORTING

Create machine-readable and human-readable research reports.

Example:

```text
Research Question
Hypothesis
Dataset
PIT Integrity
Candidate Space
Experiments Attempted
Experiments Failed
Best Candidate
Baseline
OOS Results
Execution Results
Robustness
Falsification
Multiple Testing
Replication
Researcher Degrees of Freedom
Gate Outcome
NOT_TESTED
Conclusion
```

The report must clearly distinguish:

```text
FACT
MEASUREMENT
STATISTICAL INFERENCE
ASSUMPTION
NOT_TESTED
INTERPRETATION
```

---

# 37. CLI

Add:

```text
quantlab hypothesis list
quantlab hypothesis inspect <id>
quantlab hypothesis create <...>
quantlab hypothesis compare <a> <b>

quantlab experiment list
quantlab experiment inspect <id>
quantlab experiment create <...>
quantlab experiment plan <id>
quantlab experiment run <id>
quantlab experiment cancel <id>
quantlab experiment report <id>

quantlab research discover <hypothesis>
quantlab research replicate <experiment>
quantlab research falsify <experiment>
quantlab research ablation <experiment>
quantlab research sensitivity <experiment>
quantlab research grid <family>
quantlab research compare <a> <b>
quantlab research family <id>
quantlab research multiple-testing <family>
quantlab research lineage <experiment>
quantlab research degrees-of-freedom <family>
quantlab research pareto <family>
quantlab research status
```

Use the existing CLI architecture and parser conventions.

---

# 38. DESKTOP APPLICATION

Extend the existing PySide6 desktop.

Add:

```text
Research Control
```

Suggested pages:

```text
Hypotheses
Experiments
Research Families
Discovery
Replication
Falsification
Sensitivity
Multiple Testing
Lineage
Research Reports
```

The desktop is a client of `quantlab.app`.

The UI must not:

- fit models directly
- calculate features directly
- query Parquet directly
- call DuckDB directly
- run portfolio optimization directly
- place orders
- bypass gates
- modify ledger history

All work goes through application services.

---

# 39. RESEARCH DASHBOARD

Provide a high-level view:

```text
ACTIVE HYPOTHESES
RUNNING EXPERIMENTS
COMPLETED EXPERIMENTS
FAILED EXPERIMENTS
DISCOVERIES
REPLICATIONS
FALSIFICATIONS
MULTIPLE-TEST FAMILIES
GATE OUTCOMES
NOT_TESTED ITEMS
```

Avoid gamification.

Do not use green "winning strategy" displays.

---

# 40. RESEARCH STATUS MODEL

Implement explicit statuses:

```text
DRAFT
REGISTERED
PLANNED
RUNNING
COMPLETED
FAILED
INVALID
FALSIFIED
DISCOVERED
REPLICATING
REPLICATED
ROBUST_CANDIDATE
REJECTED
SUPERSEDED
```

A status transition must be validated.

No arbitrary UI status mutation.

---

# 41. FAILURE HANDLING

Failures must be scientifically visible.

Examples:

```text
PIT failure
integrity failure
model failure
data failure
execution failure
budget exceeded
candidate invalid
statistical failure
infeasible portfolio
```

Record the failure reason.

Never silently drop failed candidates from the family.

---

# 42. CACHING

Cache only deterministic computations.

Cache keys must include all research-defining inputs.

At minimum:

```text
dataset_snapshot
experiment_config
component_identity
feature_identity
model_identity
universe_identity
time_range
random_seed
code/version identity where required
```

A cache hit must not hide that a candidate was tested.

---

# 43. REPRODUCIBILITY

Implement:

```text
same inputs
+
same snapshot
+
same code identity
+
same configuration
+
same seed
=
same result
```

Where nondeterministic algorithms exist, record nondeterminism explicitly.

Provide a reproducibility check.

---

# 44. CODE IDENTITY

Where practical, record:

```text
package_version
git_commit
configuration_hash
dataset_checksum
environment metadata
```

Do not require internet connectivity.

QUANT LAB remains local-first.

---

# 45. EXPERIMENT SERIALIZATION

Provide a portable experiment specification.

Example:

```yaml
experiment_id: EXP-0001
hypothesis_id: H-MOM-001
dataset:
  id: nse-research
  snapshot: sha256:...
feature_set:
  - momentum_20
alpha:
  id: rank_momentum_20
model:
  id: ols_mom
portfolio:
  id: mom20_topn
risk:
  id: default
execution:
  id: exec_conservative
validation:
  walk_forward: true
multiple_testing:
  family: MOM-2026-001
  method: bh
```

Use the project's existing serialization conventions if already established.

---

# 46. RESEARCH PLAN

A `ResearchPlan` should define:

```text
hypothesis
candidate space
baseline
validation protocol
execution assumptions
multiple-testing family
budget
stopping policy
replication policy
```

The plan must be frozen before execution.

Changing the plan creates a new version.

---

# 47. PRE-REGISTRATION SUPPORT

Implement a lightweight pre-registration mechanism.

A pre-registered experiment should freeze:

```text
hypothesis
primary metric
primary horizon
candidate family
selection rule
stopping rule
validation rule
```

Do not claim that this is legal/scientific preregistration in an external sense. It is an internal research-control mechanism.

---

# 48. PRIMARY VS SECONDARY METRICS

Distinguish:

```text
PRIMARY
SECONDARY
DIAGNOSTIC
```

Selection must not silently migrate from the primary metric to whichever secondary metric looks strongest.

---

# 49. RESEARCHER INTERVENTION LOG

Record manual interventions such as:

```text
candidate excluded
parameter changed
hypothesis amended
search stopped
baseline changed
execution assumption changed
universe changed
```

Manual intervention must create an audit event.

---

# 50. NO HIDDEN RESEARCH

The following are prohibited:

```text
hidden feature filtering
hidden candidate pruning
hidden hyperparameter search
hidden failed experiments
hidden multiple-test correction
hidden universe changes
hidden cost changes
hidden execution assumptions
```

If a candidate is tested, it exists in the research record.

---

# 51. RESEARCH GRAPH

Build a queryable research graph.

Example:

```text
Hypothesis
   │
   ├── Family
   │
   ├── Candidate A
   │      ├── Model A
   │      ├── Portfolio A
   │      └── Execution A
   │
   ├── Candidate B
   │      ├── Model B
   │      └── Execution B
   │
   └── Candidate C
          └── Falsified
```

Support lineage queries.

---

# 52. SCIENTIFIC DISCOVERY REPORT

Generate a report that can answer:

### What did we believe?

Hypothesis.

### Why did we believe it?

Economic rationale.

### What did we test?

Candidate family.

### What information was available?

PIT dataset snapshot.

### How much did we search?

Candidate count and degrees of freedom.

### What survived?

OOS / robustness / execution / replication.

### What failed?

Falsification and rejected candidates.

### How strong is the evidence?

Statistical and economic diagnostics.

### What remains uncertain?

`NOT_TESTED`.

### Can it be promoted?

Only the existing Research Gate decides.

---

# 53. RESEARCH QUALITY STATES

Implement a research-quality summary separate from the gate:

```text
UNEXPLORED
EXPLORATORY
DISCOVERED
WEAK
PROMISING
ROBUST
REPLICATED
FALSIFIED
INCONCLUSIVE
```

This is descriptive.

It must not override the Prompt 05 gate.

---

# 54. PROHIBITED SHORTCUTS

Do NOT:

- select the highest Sharpe without recording alternatives
- use future data for candidate selection
- inspect holdout results repeatedly
- tune parameters on holdout
- silently remove poor experiments
- use future regime labels
- reuse future adaptive state
- bypass execution research
- bypass risk
- bypass integrity
- create a second backtester
- create a second ledger
- import brokers
- introduce live trading
- fabricate NSE/NIFTY/ADV/holiday data
- silently convert `NOT_TESTED` to `PASS`

---

# 55. SAFETY

Maintain:

```text
LIVE_TRADING=false
```

The orchestration engine must never:

```text
request live order
enable broker
connect to Zerodha
connect to OpenAlgo for execution
bypass LiveSafetyGates
```

AI/LLM components, if referenced later, must be treated as research assistants only.

They may not:

```text
promote alpha
override gate
request live order
modify historical ledger
```

---

# 56. TESTING REQUIREMENTS

Add comprehensive tests.

Minimum categories:

```text
tests/orchestration/
├── test_hypothesis.py
├── test_experiment_identity.py
├── test_registry.py
├── test_lineage.py
├── test_snapshot.py
├── test_search_space.py
├── test_budget.py
├── test_stopping.py
├── test_multiple_testing.py
├── test_ablation.py
├── test_falsification.py
├── test_replication.py
├── test_sensitivity.py
├── test_parallelism.py
├── test_reproducibility.py
├── test_integrity.py
└── test_reports.py
```

Also update application/UI smoke tests.

---

# 57. REQUIRED INTEGRATION TEST

Create one end-to-end synthetic research experiment:

```text
synthetic PIT dataset
        ↓
hypothesis
        ↓
research family
        ↓
candidate grid
        ↓
momentum features
        ↓
alpha candidates
        ↓
existing model engine
        ↓
existing portfolio constructor
        ↓
existing risk engine
        ↓
existing execution research
        ↓
existing backtester
        ↓
existing validation
        ↓
multiple testing
        ↓
falsification
        ↓
research gate
        ↓
ledger
        ↓
research report
```

The result must be fully traceable.

---

# 58. ADVERSARIAL TESTS

Explicitly test:

1. Change one parameter after experiment freeze.
2. Append future data.
3. Change dataset snapshot.
4. Hide a failed candidate.
5. Alter stopping rule after seeing results.
6. Remove one poor candidate from a family.
7. Reuse holdout.
8. Change execution costs after selection.
9. Change universe after selection.
10. Mutate adaptive state across experiments.
11. Run experiments in different parallel order.
12. Delete a lineage parent.
13. Reuse an experiment ID.
14. Modify an immutable ledger result.

Expected behavior:

```text
FAIL
or
explicit immutable versioning
```

Never silent acceptance.

---

# 59. PERFORMANCE

The orchestration layer must remain lightweight.

It should coordinate existing engines rather than duplicate computations.

Use:

- deterministic caching
- process isolation where required
- controlled parallelism
- explicit budgets
- lazy report generation
- compact experiment metadata

Do not optimize prematurely.

Scientific correctness takes priority over throughput.

---

# 60. DOCUMENTATION

Create:

```text
docs/architecture/RESEARCH_ORCHESTRATION_ENGINE.md
docs/research/RESEARCH_METHODOLOGY.md
docs/research/HYPOTHESIS_MANAGEMENT.md
docs/research/EXPERIMENT_DESIGN.md
docs/research/MULTIPLE_TESTING.md
docs/research/RESEARCHER_DEGREES_OF_FREEDOM.md
docs/research/FALSIFICATION.md
docs/research/REPLICATION.md
docs/research/RESEARCH_LINEAGE.md
docs/research/SCIENTIFIC_DISCOVERY.md
docs/decisions/ADR-028-research-orchestration.md
```

---

# 61. ARCHITECTURE DOCUMENT

The architecture document must explicitly show:

```text
                    QUANT LAB
                        │
             RESEARCH CONTROL PLANE
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
   Hypothesis       Experiment       Research
    Registry          Registry         Family
        │               │                │
        └───────────────┼────────────────┘
                        ▼
                  Orchestrator
                        │
       ┌────────────────┼─────────────────┐
       ▼                ▼                 ▼
   Features           Models          Ensembles
       │                │                 │
       └────────────────┼─────────────────┘
                        ▼
                   Portfolio
                        ▼
                      Risk
                        ▼
              Execution Research
                        ▼
                  Backtester
                        ▼
                  Validation
                        ▼
              Multiple Testing
                        ▼
                  Falsification
                        ▼
                 Research Gate
                        ▼
              Existing Ledger
```

---

# 62. CLI EXAMPLE

A complete workflow should be possible conceptually:

```bash
quantlab hypothesis create momentum-hypothesis.yaml

quantlab research family create momentum-family.yaml

quantlab experiment plan EXP-0001

quantlab experiment run EXP-0001

quantlab research falsify EXP-0001

quantlab research sensitivity EXP-0001

quantlab research multiple-testing MOM-FAMILY-001

quantlab research replicate EXP-0001

quantlab experiment report EXP-0001
```

Adapt exact command syntax to the existing CLI implementation.

---

# 63. ACCEPTANCE CRITERIA

Prompt 14 is complete only when:

### Architecture

- Existing 1.3 architecture remains intact.
- No second backtester exists.
- No second PIT fabric exists.
- No second ledger exists.
- No second research gate exists.
- Orchestration remains above existing engines.

### Scientific integrity

- Hypotheses are explicit.
- Experiments are versioned.
- Candidate families are visible.
- Search spaces are recorded.
- Multiple testing is tracked.
- Stopping rules are tracked.
- Researcher degrees of freedom are visible.
- Falsification exists.
- Replication exists.
- Lineage is complete.

### Reproducibility

- Dataset snapshot is fixed.
- Configuration is hashed.
- Experiment identity is immutable.
- Random seeds are recorded.
- Code identity is recorded where available.
- Repeat execution produces equivalent results.

### Safety

```text
LIVE_TRADING=false
```

remains true.

No broker is imported by orchestration.

AI cannot override the research gate.

### Validation

- Existing Prompt 05 validation remains authoritative.
- Synthetic results remain `WARN`.
- `NOT_TESTED` remains explicit.
- Failed experiments remain visible.

### Quality

Run:

```bash
ruff check .
mypy --strict src/quantlab
pytest
```

All existing tests must continue passing.

Add sufficient orchestration tests to cover the full research lifecycle.

---

# 64. DEFINITION OF DONE

Do not report completion merely because the package imports.

Prompt 14 is complete only when QUANT LAB can demonstrate:

```text
DEFINE
  ↓
FREEZE
  ↓
SEARCH
  ↓
TEST
  ↓
COMPARE
  ↓
FALSIFY
  ↓
VALIDATE
  ↓
CORRECT FOR MULTIPLE TESTING
  ↓
REPLICATE
  ↓
REPORT
  ↓
GATE
  ↓
LEDGER
```

with complete provenance and no hidden research decisions.

The system must be capable of saying:

> **"We searched 120 candidates in this pre-defined family, 117 were rejected, 3 survived the initial discovery stage, 2 failed execution robustness, 1 survived the defined OOS and falsification tests, the multiple-testing adjustment was applied, replication is pending, and the existing research gate remains WARN."**

That is a scientifically useful result.

It is far more valuable than:

> **"Strategy X has Sharpe 4.7."**

---

# 65. FINAL ENGINEERING DIRECTIVE

Think like a quantitative researcher, statistician, software architect, and scientific-computing engineer.

Do not optimize QUANT LAB for producing attractive backtest charts.

Optimize it for producing **reproducible, falsifiable, auditable knowledge**.

The central design philosophy is:

```text
SEARCH BROADLY
        ↓
RECORD EVERYTHING
        ↓
CONTROL DEGREES OF FREEDOM
        ↓
FALSIFY AGGRESSIVELY
        ↓
VALIDATE OUT-OF-SAMPLE
        ↓
ACCOUNT FOR MULTIPLE TESTING
        ↓
REPLICATE
        ↓
ONLY THEN CONSIDER PROMOTION
```

A strategy that fails is useful.

A feature that has zero IC is useful.

A model that loses to a baseline is useful.

An ensemble that adds no incremental information is useful.

An execution model that destroys an apparent edge is useful.

A falsified hypothesis is useful.

The purpose of QUANT LAB is not to manufacture winners.

**The purpose of QUANT LAB is to discover what survives serious attempts to prove it wrong.**

---

## VERSIONING

```text
QUANT LAB BASELINE: 1.3.0
PROMPT: 14
TARGET: 1.4.0
MODULE: quantlab.orchestration
LIVE_TRADING: false
BACKTESTERS: 1
PIT_DATA_FABRICS: 1
RESEARCH_GATES: 1
EXPERIMENT_LEDGERS: 1
```

**Implement on the existing tree. Do not reset, rewrite, or remove Prompts 01–13.**
