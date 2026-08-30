# QUANT LAB — CURSOR ENGINEERING PROMPT 15
# Advanced Alpha Discovery, Genetic Search & Symbolic Quant Research Engine

**Target release:** QUANT LAB 1.5.0  
**Prompt:** 15  
**Status:** Engineering specification — implement on the EXISTING QUANT LAB 1.4.0 tree  
**Primary objective:** Build a research-grade alpha discovery engine for generating, evolving, evaluating, falsifying, deduplicating, and validating candidate mathematical expressions under strict point-in-time and scientific-research controls.

---

## 0. EXECUTION DIRECTIVE

You are implementing **Prompt 15** inside the existing QUANT LAB repository.

This is NOT a greenfield project.

You MUST first inspect the existing repository and understand Prompts 01–14, especially:

- Point-in-Time Data Fabric
- `MarketState`
- feature/label separation
- alpha engine
- portfolio construction
- factor/risk engine
- regime engine
- adaptive learning
- statistical learning
- ensemble/meta-alpha engine
- execution-research engine
- research orchestration/control plane
- Prompt 05 research gate
- canonical `run_backtest`
- JSONL experiment ledger
- integrity framework
- desktop `quantlab.app` boundary
- `LiveSafetyGates`

### HARD RULE

**Do not rewrite working architecture merely to introduce Prompt 15.**

Extend existing abstractions where appropriate.

Do not create:

- a second PIT fabric
- a second backtester
- a second portfolio optimizer
- a second covariance engine
- a second FDR/multiple-testing engine
- a second experiment ledger
- a second research gate
- a broker integration
- a live trading path

Prompt 15 is a **research discovery layer**.

It generates research candidates.

It does NOT create orders.

It does NOT place trades.

It does NOT promote candidates.

---

# 1. CORE RESEARCH QUESTION

Prompt 15 must answer:

> **Can QUANT LAB systematically discover novel mathematical relationships between PIT-available information at decision time T and future market behavior, while controlling expression complexity, data mining, redundancy, multiple testing, temporal leakage, and researcher degrees of freedom?**

The engine must distinguish:

```text
DISCOVERY
    ≠
CONFIRMATION
    ≠
VALIDATION
    ≠
REPLICATION
    ≠
PROMOTION
```

And:

```text
FEATURE
    ≠
FACTOR
    ≠
ALPHA
    ≠
MODEL
    ≠
DISCOVERED EXPRESSION
    ≠
STRATEGY
    ≠
PORTFOLIO
    ≠
ORDER
```

A discovered expression is a **research hypothesis** until independently validated.

---

# 2. NON-NEGOTIABLE SCIENTIFIC PRINCIPLE

The engine MUST NOT optimize directly for:

```text
maximum Sharpe
maximum return
minimum drawdown
maximum in-sample IC
```

without simultaneously accounting for:

- complexity
- turnover
- correlation with existing signals
- temporal stability
- walk-forward performance
- statistical significance
- multiple testing
- discovery count
- search-space size
- effective number of trials
- data availability
- execution assumptions
- null/falsification tests

A spectacular in-sample expression that fails OOS is a **successful falsification result**, not a successful alpha.

---

# 3. ARCHITECTURAL POSITION

The system must become:

```text
PIT DATA FABRIC
      │
      ▼
FEATURE ENGINE / FACTOR ENGINE
      │
      ▼
ALPHA ENGINE
      │
      ▼
MODEL / ADAPTIVE / ENSEMBLE
      │
      ▼
┌──────────────────────────────────────────────┐
│       PROMPT 15 — ALPHA DISCOVERY            │
│                                              │
│  Research Grammar                            │
│       ↓                                      │
│  Candidate Generator                         │
│       ↓                                      │
│  Expression Genome                           │
│       ↓                                      │
│  Symbolic / Genetic Search                   │
│       ↓                                      │
│  Complexity + Validity Filter                │
│       ↓                                      │
│  PIT Evaluation                              │
│       ↓                                      │
│  Falsification                               │
│       ↓                                      │
│  Novelty / Redundancy Analysis               │
│       ↓                                      │
│  Walk-Forward Validation                     │
│       ↓                                      │
│  Multiple Testing via Prompt 14              │
│       ↓                                      │
│  Replication Candidate                       │
└──────────────────────────────────────────────┘
      │
      ▼
PROMPT 14 RESEARCH ORCHESTRATION
      │
      ▼
PROMPT 05 RESEARCH GATE
      │
      ▼
PORTFOLIO CONSTRUCTION
      │
      ▼
EXECUTION RESEARCH
      │
      ▼
CANONICAL BACKTEST
      │
      ▼
LEDGER
```

Prompt 15 must integrate with this graph rather than duplicate it.

---

# 4. PACKAGE

Create:

```text
src/quantlab/discovery/
```

Recommended internal architecture:

```text
quantlab/discovery/
├── __init__.py
├── definitions.py
├── grammar.py
├── operators.py
├── primitives.py
├── expression.py
├── ast.py
├── genome.py
├── generator.py
├── mutation.py
├── crossover.py
├── population.py
├── fitness.py
├── constraints.py
├── evaluator.py
├── search.py
├── symbolic.py
├── genetic.py
├── novelty.py
├── redundancy.py
├── complexity.py
├── falsification.py
├── validation.py
├── archive.py
├── lineage.py
├── registry.py
├── reproducibility.py
├── integrity.py
└── errors.py
```

Keep `__init__.py` thin.

Avoid circular imports.

---

# 5. EXPRESSION REPRESENTATION

Every discovered alpha MUST be represented as a typed, serializable expression tree / AST.

Example:

```text
rank(
    zscore(
        sub(
            momentum_20,
            rolling_mean(volatility_20, 10)
        )
    )
)
```

The AST must preserve:

- operator
- operands
- parameter values
- parameter ranges
- feature identities
- versions
- transformations
- normalization
- universe
- frequency
- expression hash
- parent expressions
- generation
- mutation history
- crossover history
- search run
- random seed

Two mathematically equivalent expressions should be canonicalized where possible.

Example:

```text
add(x, y)
```

and

```text
add(y, x)
```

should have the same canonical identity if `add` is commutative.

---

# 6. TYPE SYSTEM

Do not permit arbitrary invalid expression trees.

Define explicit types such as:

```text
Scalar
CrossSection
TimeSeries
Panel
Boolean
RankedCrossSection
ReturnSeries
VolatilitySeries
```

Operators must declare:

```text
input_types
output_type
parameter_schema
lookback_requirements
missing_value_policy
mathematical_domain
```

Invalid compositions MUST raise a typed discovery error.

Never silently coerce invalid types.

---

# 7. PRIMITIVE LIBRARY

Build a controlled primitive library.

### Price primitives

```text
open
high
low
close
volume
returns_1
returns_N
```

Only if the source dataset actually provides them.

### Existing feature references

The discovery engine should be able to consume registered features from Prompt 06.

Examples:

```text
momentum_5
momentum_10
momentum_20
rolling_std_20
rolling_mean_20
```

Do NOT duplicate feature calculations.

### Cross-sectional transforms

```text
rank
zscore
winsorize
demean
neutralize_if_supported
quantile
sign
abs
```

### Time-series transforms

```text
rolling_mean
rolling_std
rolling_min
rolling_max
rolling_sum
ewma
change
delta
lag
```

### Mathematical transforms

```text
add
sub
mul
div
neg
sqrt
log
exp
pow
abs
min
max
```

Domain-safe versions MUST be used.

For example:

```text
log(x)
```

must never blindly evaluate `log(x <= 0)`.

Use explicit domain semantics.

---

# 8. LOOKAHEAD SAFETY

This is one of the highest-priority requirements.

At decision time:

```text
T
```

an expression may use only information available at:

```text
available_time <= T
```

The evaluator MUST propagate availability metadata through the expression tree.

For every node maintain:

```text
effective_available_time
```

For an expression:

```text
f(x, y)
```

the output cannot be available earlier than:

```text
max(availability(x), availability(y))
```

If an expression requires unavailable information:

```text
IntegrityStatus = FAIL
```

Never silently drop the candidate and hide the reason.

---

# 9. LABEL ISOLATION

Forward labels belong to evaluation only.

Examples:

```text
future_return
forward_volatility
future_drawdown
future_hit
```

MUST NOT appear as primitives available to candidate generation.

If a label enters an expression:

```text
label_as_feature = FAIL
```

The candidate must be quarantined.

---

# 10. PIT EVALUATION

Every candidate must be evaluated against a specific immutable dataset snapshot.

Required identity:

```text
dataset_id
dataset_version
snapshot_checksum
universe_id
universe_as_of_policy
frequency
range
decision_time_definition
feature_versions
expression_hash
```

Appending future data MUST NOT change historical expression values.

This must be tested explicitly.

---

# 11. EXPRESSION GRAMMAR

Implement a configurable grammar.

Example:

```text
Expression :=
    Primitive
  | Unary(Expression)
  | Binary(Expression, Expression)
  | Rolling(Expression, Window)
  | CrossSection(Expression)
```

Grammar must support restrictions such as:

```text
max_depth
max_nodes
max_features
max_constants
max_nested_transforms
allowed_operators
allowed_features
allowed_windows
```

Do not permit unrestricted symbolic explosion.

---

# 12. COMPLEXITY CONTROL

Every expression gets a complexity score.

At minimum include:

```text
node_count
tree_depth
operator_count
feature_count
constant_count
nested_transform_count
lookback_span
```

Example:

```text
complexity_score =
    w1 * nodes
  + w2 * depth
  + w3 * operators
  + w4 * constants
  + w5 * feature_count
```

Weights must be configurable and versioned.

Complexity must be recorded in the experiment ledger.

Prefer simpler expressions when predictive information is comparable.

---

# 13. GENOME REPRESENTATION

Implement an explicit genome representation.

Each genome must contain:

```text
genome_id
expression_ast
canonical_expression
expression_hash
generation
parent_ids
mutation_operator
crossover_parent_ids
random_seed
complexity
fitness
research_run_id
```

Genome identity must be deterministic.

Same:

```text
expression + grammar_version + feature_versions
```

should produce the same canonical identity.

---

# 14. INITIAL CANDIDATE GENERATION

Support:

### Random generation

Generate valid expressions from the grammar.

### Seeded generation

Allow predefined mathematical seeds.

Example:

```text
momentum_20
rank(momentum_20)
zscore(momentum_20)
rank(momentum_20 - volatility_20)
rank(momentum_20 / volatility_20)
```

### Human hypothesis

Allow a researcher to submit an explicit expression for evaluation.

The system must treat human-created and machine-generated candidates consistently in the ledger.

---

# 15. GENETIC SEARCH

Implement genetic programming primitives:

```text
selection
elitism
mutation
crossover
replacement
population_generation
```

Selection methods may include:

```text
tournament
rank
roulette
```

But all must be deterministic under a fixed seed.

---

# 16. MUTATION

Implement safe mutation operators:

```text
replace_operator
replace_feature
replace_window
replace_constant
subtree_mutation
wrap_unwrap_transform
negate
simplify
```

Every mutation must create a new immutable expression identity.

Never mutate an archived candidate in place.

---

# 17. CROSSOVER

Implement subtree crossover.

Constraints:

- resulting tree must remain type-valid
- max depth cannot be exceeded
- max nodes cannot be exceeded
- domain-invalid expressions are rejected
- feature/label boundaries remain intact

Record both parent IDs.

---

# 18. SEARCH OBJECTIVE

Do NOT use raw Sharpe as the sole objective.

Implement a multi-objective fitness framework.

At minimum:

```text
predictive_score
complexity_penalty
redundancy_penalty
turnover_penalty
stability_score
coverage_score
```

Possible predictive scores:

```text
mean IC
median IC
rank IC
quantile spread
OOS predictive score
```

The actual fitness function must be versioned.

---

# 19. MULTI-OBJECTIVE SEARCH

Support Pareto-style selection.

Objectives may include:

```text
maximize predictive_score
maximize stability
maximize coverage
maximize novelty
minimize complexity
minimize redundancy
minimize turnover
```

Do not collapse everything into a single score unless explicitly configured.

Record:

```text
objective_vector
pareto_rank
dominance_count
```

---

# 20. NOVELTY SEARCH

A discovered expression should not be considered valuable merely because it is highly correlated with an existing alpha.

Calculate similarity using:

- expression structure
- feature overlap
- output correlation
- rank correlation
- IC profile similarity
- factor exposure similarity where available

Classify:

```text
NOVEL
LOW_REDUNDANCY
MODERATE_REDUNDANCY
HIGH_REDUNDANCY
DUPLICATE
```

Do not use future information to determine novelty.

---

# 21. ALPHA REDUNDANCY

Reuse Prompt 12/Prompt 08 statistical infrastructure where appropriate.

Do not create another correlation engine.

Compare discovered candidates against:

```text
existing alphas
existing ensembles
existing factors
existing known features
archived discoveries
```

A candidate that is effectively:

```text
rank(momentum_20)
```

with cosmetic mathematical transformations should be identified as redundant where canonicalization permits.

---

# 22. SYMBOLIC SIMPLIFICATION

Implement conservative symbolic simplification.

Examples:

```text
x + 0 → x
x * 1 → x
x - 0 → x
-x → neg(x)
```

Do not perform algebraic simplifications that change domain semantics.

Simplification must preserve:

```text
availability
missing-value behavior
numerical domain
expression identity lineage
```

---

# 23. NUMERICAL STABILITY

Candidate evaluation must detect:

```text
division_by_zero
near_zero_denominator
overflow
underflow
NaN
inf
invalid_log
invalid_sqrt
explosive_values
constant_expression
zero_variance
```

A candidate with invalid numerical behavior must be flagged.

Never silently convert:

```text
NaN → 0
inf → 0
```

unless the expression definition explicitly specifies that behavior.

---

# 24. MISSING DATA POLICY

Default:

```text
missing = unavailable
```

Not:

```text
missing = 0
```

Coverage must be reported.

Candidate metrics must include:

```text
observations
available_observations
coverage
missing_count
invalid_count
```

A candidate with insufficient coverage must not appear successful.

---

# 25. CONSTANT / DEGENERATE CANDIDATES

Detect and quarantine:

```text
constant expressions
near-constant expressions
zero-variance signals
single-name dominance
single-day dominance
extreme sparse signals
```

These are valid research outcomes but not valid alpha candidates.

---

# 26. FALSIFICATION ENGINE

Every serious discovery run must include adversarial tests.

At minimum:

### Sign reversal

```text
alpha
vs
-alpha
```

### Feature permutation

Destroy cross-sectional information where appropriate.

### Temporal permutation

Use only in explicitly defined diagnostic contexts.

### Label permutation

Destroy signal-label relationship.

### Null expression

Compare against no-signal baseline.

### Complexity ablation

Simplify expression and compare.

### Feature ablation

Remove major primitives and measure degradation.

### Subtree ablation

Remove important expression branches.

The system must record whether the candidate survives.

---

# 27. DISCOVERY ≠ CONFIRMATION

The search engine MUST NOT use the same observations to both:

```text
discover
and
declare confirmed
```

Implement explicit stages:

```text
DISCOVERY
    ↓
QUARANTINE
    ↓
CONFIRMATION
    ↓
OOS VALIDATION
    ↓
REPLICATION
```

Prompt 14 orchestrates the overall experiment.

Prompt 15 supplies candidates and discovery metadata.

---

# 28. WALK-FORWARD DISCOVERY

Search itself must respect time.

Do not:

```text
fit/search on all history
then replay historically
```

for predictive discovery.

Use:

```text
TRAIN/DISCOVERY WINDOW
        ↓
FREEZE
        ↓
FORWARD TEST WINDOW
        ↓
REALIZE
        ↓
UPDATE DISCOVERY STATE
```

No future OOS information may influence prior candidate generation.

---

# 29. SEARCH STATE

Persist immutable search-state checkpoints.

Each checkpoint records:

```text
search_run_id
generation
population
fitness
archive
random_seed
grammar_version
feature_snapshot
dataset_snapshot
configuration_hash
```

This allows exact research reproduction.

---

# 30. SEARCH REPRODUCIBILITY

Given identical:

```text
dataset snapshot
grammar
feature versions
search configuration
random seed
software version
```

the search must produce the same candidate sequence or a documented deterministic equivalent.

Hash all relevant configuration.

---

# 31. COMPUTATIONAL BUDGET

Implement explicit budgets.

Examples:

```text
max_candidates
max_generations
max_evaluations
max_runtime
max_expression_nodes
max_population
```

Never allow an accidental infinite search.

Record:

```text
budget_requested
budget_consumed
budget_exhausted
stopping_reason
```

---

# 32. STOPPING RULES

Stopping must be pre-specified.

Allowed:

```text
generation_limit
candidate_limit
evaluation_limit
runtime_limit
convergence
stability_plateau
```

Do NOT stop because:

```text
current Sharpe looks good
current IC looks good
candidate is profitable
```

unless that stopping rule was explicitly pre-registered.

Prompt 14 must be able to detect:

```text
posthoc_stopping
```

---

# 33. MULTIPLE TESTING

This is mandatory.

Every generated candidate is a research trial.

Record:

```text
tested_count
candidate_family
search_space_id
discovery_run_id
```

Reuse Prompt 14's multiple-testing infrastructure.

Do not create a second FDR engine.

Support the existing:

```text
BH
Bonferroni
Holm
```

and any future Prompt 14 methods.

Search results must not be represented as if only the winning candidate had been tested.

---

# 34. EFFECTIVE SEARCH SIZE

Track both:

```text
raw_candidate_count
unique_candidate_count
```

and, where possible:

```text
duplicate_count
correlated_cluster_count
effective_candidate_count
```

Do not claim that highly correlated candidates are independent tests.

Document the approximation used.

---

# 35. FAMILY-WISE DISCOVERY

Every search belongs to a named family.

Example:

```text
family_id = GP-MOM-VOL-001
```

Family definition includes:

```text
allowed_features
allowed_operators
allowed_windows
max_depth
max_nodes
population
generations
selection
mutation_rates
crossover_rate
fitness_definition
constraints
```

Changing the search family definition creates a new immutable identity.

---

# 36. RESEARCH LINEAGE

Every candidate must be traceable:

```text
hypothesis
    ↓
research experiment
    ↓
search family
    ↓
generation
    ↓
parent candidates
    ↓
mutations/crossover
    ↓
expression
    ↓
evaluation
    ↓
falsification
    ↓
validation
```

No orphan candidate should exist.

---

# 37. DISCOVERY ARCHIVE

Implement an archive containing:

```text
candidate_id
expression
metrics
complexity
novelty
redundancy
stability
falsification_status
validation_status
research_gate_status
lineage
```

Archive:

```text
best predictive
best simple
best novel
best stable
best low-turnover
Pareto frontier
```

Do not archive only the maximum-Sharpe candidate.

---

# 38. ALPHA MATERIALIZATION

A discovered expression may be materialized into a Prompt 06/07-compatible research alpha only through an explicit conversion step.

Example:

```text
quantlab discovery materialize <candidate>
```

This must create a versioned alpha identity.

The system must not silently promote:

```text
candidate → alpha
```

Materialization should require:

```text
candidate status
validation status
expression identity
feature dependencies
```

---

# 39. PORTFOLIO BOUNDARY

Prompt 15 does not construct production portfolios.

It may evaluate:

```text
cross-sectional predictive properties
```

but final portfolio weights remain owned by:

```text
quantlab.portfolio
```

No broker import.

No order generation.

No OMS calls.

---

# 40. BACKTEST BOUNDARY

Prompt 15 does not create a second P&L engine.

If a discovered alpha needs strategy-level validation:

```text
Prompt 14 orchestration
        ↓
Prompt 07 portfolio construction
        ↓
canonical run_backtest
        ↓
Prompt 05 gate
```

Reuse the canonical pipeline.

---

# 41. EXECUTION BOUNDARY

Prompt 15 does not simulate broker execution directly.

Execution realism remains:

```text
quantlab.execution_research
```

If discovery candidates are evaluated under execution assumptions, invoke the existing research layer through orchestration.

---

# 42. RISK BOUNDARY

Risk/factor exposure analysis remains owned by:

```text
quantlab.risk
quantlab.factor
```

Prompt 15 may request risk diagnostics.

It must not duplicate the risk model.

---

# 43. REGIME BOUNDARY

Prompt 15 may conditionally evaluate expressions by existing regime labels.

It must not fit hindsight regimes.

Use Prompt 09.

Predictive regime context must obey existing temporal rules.

---

# 44. ADAPTIVE LEARNING BOUNDARY

Prompt 15 may generate candidates for Prompt 10 adaptive learners.

It must not modify adaptive learner state.

Do not allow future learner performance to influence historical candidate discovery.

---

# 45. MODEL BOUNDARY

Prompt 15 generates mathematical expressions.

It is not:

```text
quantlab.learning
```

A discovered expression can later become a model input.

Do not merge the two concepts.

---

# 46. ENSEMBLE BOUNDARY

Prompt 15 may generate multiple independent candidates.

Combination remains owned by:

```text
quantlab.ensemble
```

The discovery engine may provide a candidate correlation matrix request but must not implement a second ensemble optimizer.

---

# 47. PROMPT 14 INTEGRATION

Prompt 14 is the research control plane.

Prompt 15 must integrate with it for:

```text
experiment identity
hypothesis identity
search family
candidate count
selection policy
multiple testing
replication
falsification
lineage
degrees of freedom
reporting
```

Do not recreate those concepts unnecessarily.

---

# 48. PROMPT 05 GATE

Prompt 05 remains the ONLY promotion gate.

Discovery cannot override:

```text
REJECT
WARN
RESEARCH_CANDIDATE
PROMOTED_TO_PAPER
```

No discovery-specific promotion gate may compete with Prompt 05.

Synthetic data must remain incapable of becoming:

```text
RESEARCH_CANDIDATE
```

or:

```text
PROMOTED_TO_PAPER
```

---

# 49. LIVE SAFETY

This requirement is absolute:

```text
LIVE_TRADING = false
```

Prompt 15 must not:

```text
import broker modules
request live orders
request paper orders
bypass LiveSafetyGates
modify broker configuration
enable live mode
```

AI cannot use discovery results to request a live order.

Any attempted live path must fail closed.

---

# 50. RESEARCH MODES

Support explicit modes:

```text
discovery
falsification
confirmation
replication
benchmark
null_test
```

Default:

```text
discovery
```

Mode must be recorded in every experiment.

---

# 51. SEARCH ALGORITHMS

Implement at least:

```text
random_search
genetic_programming
evolutionary_search
```

Provide a clean interface so future algorithms can be added:

```text
SymbolicRegressionEngine
SearchAlgorithm
PopulationStrategy
FitnessEvaluator
MutationOperator
CrossoverOperator
SelectionOperator
```

Do not hard-code one algorithm into the entire package.

---

# 52. SYMBOLIC REGRESSION

Provide a constrained symbolic regression mode.

Objective:

```text
find expression f(X)
```

such that:

```text
f(X_T)
```

contains useful information about:

```text
Y_(T+H)
```

subject to:

```text
PIT safety
complexity
coverage
stability
redundancy
search budget
multiple testing
```

Do not depend on external symbolic-regression packages unless absolutely necessary.

Prefer an internal deterministic AST-based implementation initially.

---

# 53. CONSTANT HANDLING

Constants must be explicit.

Example:

```text
x / 20
x * 0.5
```

Constants become part of the search space.

Track:

```text
constant_count
constant_values
constant_search_policy
```

Avoid unconstrained real-valued constant evolution.

Use bounded, configurable constant grids initially.

---

# 54. LOOKBACK SEARCH

Support configurable windows:

```text
2
3
5
10
20
30
60
120
```

But every tested window is part of the search space.

Do not hide the number of combinations.

---

# 55. FEATURE SEARCH

Candidate generation may select among registered features.

Every feature dependency must include:

```text
feature_id
feature_version
snapshot
availability
```

If a feature definition changes, candidate identity changes.

---

# 56. FEATURE FAMILY CONSTRAINTS

Support:

```text
allow_price_features
allow_volume_features
allow_volatility_features
allow_momentum_features
allow_regime_features
allow_factor_features
```

But do not permit future-derived labels.

---

# 57. CROSS-SECTIONAL SAFETY

Cross-sectional transforms must use only the universe valid at T.

Never use:

```text
today's universe
```

for historical T.

Use:

```text
universe.as_of(T)
```

and existing PIT identity rules.

---

# 58. SURVIVORSHIP

Do not silently claim survivorship safety.

If historical membership is unavailable:

```text
survivorship = NOT_TESTED
```

Do not fabricate NIFTY membership.

---

# 59. CORPORATE ACTIONS

Do not invent adjustment data.

If corporate-action announcement/effective timing is unknown:

```text
corporate_action_integrity = NOT_TESTED
```

---

# 60. SEARCH DATA SPLITS

Support:

```text
discovery
validation
holdout
replication
```

The holdout must remain untouched until the explicitly registered stage.

Any holdout contamination:

```text
FAIL
```

---

# 61. RESEARCH QUARANTINE

Candidates with any of the following should be quarantined:

```text
integrity_fail
numerical_instability
insufficient_coverage
duplicate
future_leak
label_leak
future_normalization
future_universe
over_complex
budget_violation
```

Quarantine reason must be machine-readable.

---

# 62. CANDIDATE STATUS MACHINE

Implement:

```text
GENERATED
VALIDATED_SYNTAX
EVALUATED
QUARANTINED
FALSIFIED
DISCOVERY_SURVIVOR
CONFIRMATION_PENDING
OOS_SURVIVOR
REPLICATION_PENDING
REPLICATED
REJECTED
MATERIALIZABLE
```

Do not allow illegal state transitions.

---

# 63. DISCOVERY METRICS

At minimum calculate:

```text
IC mean
IC median
IC std
IC hit rate
IC decay
quantile spread
coverage
turnover proxy
complexity
novelty
redundancy
stability
OOS score
```

Reuse Prompt 06/08/10/11 metrics where possible.

---

# 64. TEMPORAL STABILITY

Measure performance by:

```text
rolling windows
walk-forward folds
regime
market state
```

Do not evaluate stability using future information unavailable at the evaluation timestamp.

---

# 65. DECAY ANALYSIS

Measure:

```text
IC decay
performance decay
parameter sensitivity
window sensitivity
```

A discovery whose effect disappears immediately should be flagged:

```text
DECAY_HIGH
```

not silently rejected.

---

# 66. SENSITIVITY ANALYSIS

Automatically test nearby parameter values where pre-registered.

Example:

```text
momentum window:
18
20
22
```

The original candidate must remain identified separately from sensitivity variants.

Do not replace the original identity.

---

# 67. ABLATION

Support:

```text
feature ablation
operator ablation
subtree ablation
complexity ablation
```

Question:

> Does the discovered relationship actually depend on the claimed structure?

---

# 68. NULL BENCHMARKS

Every discovery family should have an explicit baseline.

Examples:

```text
no_signal
random_expression
sign_reversed
permuted_label
simplified_expression
best_simple_baseline
```

Use existing Prompt 06/11/14 infrastructure.

---

# 69. RESEARCH REPORT

Every completed discovery run must produce a machine-readable and human-readable report.

Required sections:

```text
1. Research question
2. Hypothesis
3. Dataset
4. PIT snapshot
5. Search family
6. Grammar
7. Search budget
8. Candidate count
9. Unique candidate count
10. Selection policy
11. Best predictive candidates
12. Best simple candidates
13. Pareto frontier
14. Redundancy analysis
15. Falsification results
16. Walk-forward results
17. Multiple-testing correction
18. Holdout status
19. Execution sensitivity
20. Risk/factor diagnostics
21. Replication status
22. Integrity status
23. Gate outcome
24. NOT_TESTED
25. Lineage
```

---

# 70. CLI

Add:

```bash
quantlab discovery list
quantlab discovery inspect <candidate>
quantlab discovery generate <family>
quantlab discovery search <family>
quantlab discovery evolve <run>
quantlab discovery evaluate <candidate>
quantlab discovery mutate <candidate>
quantlab discovery crossover <candidate-a> <candidate-b>
quantlab discovery simplify <candidate>
quantlab discovery archive <run>
quantlab discovery lineage <candidate>
quantlab discovery falsify <candidate>
quantlab discovery validate <candidate>
quantlab discovery replicate <candidate>
quantlab discovery report <run>
quantlab discovery compare <candidate-a> <candidate-b>
quantlab discovery pareto <run>
quantlab discovery redundancy <run>
quantlab discovery complexity <candidate>
quantlab discovery sensitivity <candidate>
```

Research aliases:

```bash
quantlab research discover
quantlab research symbolic
quantlab research genetic
quantlab research falsification
quantlab research alpha-discovery
quantlab research novelty
quantlab research expression
quantlab research discovery-family
```

Do not break existing CLI commands.

---

# 71. DESKTOP INTEGRATION

Add:

```text
Discovery Lab
```

to the existing desktop navigation.

The UI must be a viewer/controller of `quantlab.app`.

It must NOT:

- evaluate expressions directly
- run genetic search in the Qt process
- parse Parquet directly
- access brokers
- mutate ledger rows
- bypass PIT
- bypass Prompt 14
- bypass Prompt 05

Recommended pages:

```text
Discovery Overview
Search Runs
Candidate Explorer
Expression Tree
Fitness / Pareto
Falsification
Novelty / Redundancy
Lineage
Validation
Research Report
```

Long-running searches must execute outside the UI process.

---

# 72. APP LAYER

Extend:

```text
quantlab.app
```

with query/job interfaces.

Examples:

```text
DiscoveryService
DiscoveryQuery
DiscoveryJob
DiscoveryReportQuery
CandidateQuery
```

The desktop remains decoupled from computational internals.

---

# 73. LEDGER

Reuse the existing JSONL ledger.

Do not create:

```text
discovery_ledger.jsonl
```

unless the architecture already explicitly requires a separate storage layer.

Prefer extending existing ledger records with optional fields.

Record:

```text
selection_stage = "discovery"
research_type = "symbolic_alpha_discovery"
discovery_run_id
candidate_id
family_id
generation
tested_count
unique_candidate_count
search_space_id
search_policy
expression_hash
complexity_score
novelty_score
redundancy_score
falsification_status
```

Old rows must continue to load.

---

# 74. IMMUTABILITY

Once a candidate is archived:

```text
expression
metrics
lineage
dataset snapshot
configuration
```

must be immutable.

A new evaluation produces a new version.

Never overwrite historical research evidence.

---

# 75. ERROR TYPES

Create explicit exceptions such as:

```text
DiscoveryError
InvalidExpression
ExpressionTypeError
ExpressionDomainError
DiscoveryIntegrityError
SearchBudgetExceeded
InvalidGenome
GenomeConstraintError
CandidateQuarantined
DiscoveryStateError
DuplicateCandidate
HoldoutContamination
```

Errors must be actionable.

---

# 76. INTEGRITY FLAGS

Add Prompt 15 integrity checks without replacing earlier checks.

At minimum:

```text
future_expression_input
future_candidate_generation
future_search_state
future_fitness
future_selection
future_mutation
future_crossover
future_feature
future_normalization
future_universe
label_as_feature
holdout_contamination
posthoc_search_budget
posthoc_stopping
hidden_candidate
search_space_omission
candidate_lineage_break
expression_mutation
future_redundancy
future_novelty
future_complexity_selection
```

Rules:

```text
explicit leak → FAIL
unknown evidence → NOT_TESTED
verified safe → PASS
```

Never convert unknown into PASS.

---

# 77. ADVERSARIAL TESTING

Create tests that intentionally inject:

```text
future feature
future label
future normalization
future universe
future fitness
future selection
future stopping
future search state
```

Every one must fail.

---

# 78. SYNTHETIC TEST FIXTURE

Create controlled synthetic datasets.

At least:

```text
known_linear_alpha
known_nonlinear_alpha
null_market
noise_market
redundant_alpha
unstable_alpha
regime_dependent_alpha
```

Synthetic fixtures must be clearly tagged:

```text
data_kind = synthetic
```

They are architecture tests, not market evidence.

---

# 79. KNOWN-ALPHA RECOVERY

The engine should be able to recover simple planted relationships under controlled synthetic data.

Example:

```text
y = 2*x1 - x2 + noise
```

The engine should recover a mathematically related expression.

Do not require exact textual expression equality when equivalent expressions exist.

Evaluate semantic equivalence where practical.

---

# 80. NULL TEST

On a pure-null synthetic dataset:

```text
discovery should not systematically manufacture convincing alpha
```

The test should inspect:

```text
selection bias
false discoveries
multiple-testing handling
```

Do not expect exactly zero apparent correlations.

The purpose is to verify that the system identifies them as discoveries subject to statistical uncertainty rather than as confirmed alpha.

---

# 81. REDUNDANCY TEST

Seed:

```text
x
rank(x)
zscore(x)
scale(x, 2)
```

The system should recognize high structural/output redundancy where appropriate.

---

# 82. COMPLEXITY TEST

Given:

```text
x
```

and:

```text
((((x + 0) * 1) + 0) ...)
```

the system should favor the simpler equivalent expression.

---

# 83. SEARCH REPRODUCIBILITY TEST

Run the same search twice with:

```text
same seed
same snapshot
same configuration
```

Expected:

```text
same candidate identities
same generation lineage
same results
```

subject to documented deterministic numerical tolerances.

---

# 84. FUTURE-DATA IMMUTABILITY TEST

Evaluate candidate values on snapshot A.

Append future data.

Re-evaluate historical timestamps.

Expected:

```text
historical values unchanged
```

Failure:

```text
FAIL
```

---

# 85. MULTIPLE-TESTING TEST

Generate a family of many null candidates.

The system must record:

```text
tested_count
family
selection policy
multiple-testing method
```

It must not report the best raw candidate as though it were an independently tested hypothesis.

---

# 86. HOLDOUT TEST

Any candidate selected using validation data must be prevented from being described as holdout-confirmed.

Explicit contamination:

```text
FAIL
```

---

# 87. PERFORMANCE REQUIREMENT

Initial implementation should prioritize:

```text
correctness
determinism
auditability
PIT safety
```

over maximum search speed.

However, design interfaces so vectorized/batched evaluation can be added later.

Do not prematurely introduce distributed infrastructure.

---

# 88. CACHING

Cache expression evaluation only when identity is complete.

Cache key must include:

```text
snapshot
dataset
feature versions
expression hash
universe
frequency
range
configuration
```

Future data must not invalidate historical correctness.

---

# 89. PARALLELISM

If parallel candidate evaluation is implemented:

- deterministic seeds
- isolated state
- no shared mutable experiment state
- deterministic result ordering
- no cross-process broker imports
- no hidden state mutation

Parallelism must never compromise reproducibility.

---

# 90. MEMORY / RESOURCE SAFETY

Prevent:

```text
unbounded population
unbounded AST depth
unbounded candidate archive
unbounded cache
```

Provide explicit limits.

---

# 91. SECURITY / SAFETY

Expressions must be data structures, not executable Python.

Never:

```text
eval(expression_string)
exec(expression_string)
```

Do not permit arbitrary code execution through the symbolic grammar.

Expression operators must map to approved internal functions.

---

# 92. VERSIONING

Increment:

```text
__version__ = "1.5.0"
```

Only after the implementation and tests are complete.

Create:

```text
ADR-029
```

and:

```text
docs/architecture/ALPHA_DISCOVERY_ENGINE.md
docs/research/GENETIC_ALPHA_DISCOVERY.md
docs/research/SYMBOLIC_RESEARCH.md
docs/research/ALPHA_DISCOVERY_VALIDATION.md
docs/research/SEARCH_BIAS_AND_MULTIPLE_TESTING.md
docs/research/EXPRESSION_COMPLEXITY.md
```

---

# 93. ARCHITECTURE DOCUMENT

ADR-029 must explicitly document:

```text
why discovery is separate from alpha
why discovery is separate from orchestration
why discovery does not own the backtester
why discovery does not own multiple-testing correction
why discovery cannot promote
why symbolic expressions require typed ASTs
why search history is immutable
why candidate count is part of evidence
```

---

# 94. DO NOT BUILD

Prompt 15 must NOT implement:

```text
live trading
broker execution
Zerodha integration
OpenAlgo order placement
autonomous trading agent
LLM trader
RL trader
production portfolio optimizer
second backtester
second risk engine
second factor engine
second covariance engine
second FDR engine
second ledger
cloud/distributed research cluster
```

Those are outside this prompt.

---

# 95. AI BOUNDARY

AI/LLM systems may assist with:

```text
hypothesis wording
expression explanation
research report summarization
candidate interpretation
research navigation
```

They must NOT:

```text
bypass integrity
modify frozen experiment specs
alter historical results
hide failed candidates
change selection policy after observing results
request live orders
```

AI suggestions are research inputs, not authoritative scientific conclusions.

---

# 96. SCIENTIFIC DISCOVERY PRINCIPLE

The system must preserve failed research.

For example:

```text
Candidate A → FAIL
Candidate B → weak
Candidate C → redundant
Candidate D → unstable
Candidate E → promising but OOS FAIL
Candidate F → survives
```

All six are evidence.

Never retain only F.

---

# 97. REQUIRED RESEARCH GRAPH

Build lineage so the system can answer:

> Where did this alpha come from?

Example:

```text
H-MOM-001
   │
   └── MOM-FAMILY-002
          │
          ├── Generation 0
          │     ├── candidate-001
          │     ├── candidate-002
          │     └── candidate-003
          │
          ├── Generation 1
          │     ├── candidate-014
          │     │      ├── parent-002
          │     │      └── parent-007
          │     └── candidate-015
          │
          └── Pareto Archive
                 └── candidate-014
```

The lineage must be machine-queryable.

---

# 98. RESEARCH QUESTIONS THE ENGINE MUST SUPPORT

Examples:

### Q1
Does a nonlinear transformation of momentum contain incremental information?

### Q2
Does combining momentum and volatility nonlinearly improve OOS IC?

### Q3
Can a low-complexity expression outperform a more complex expression after costs?

### Q4
Does a discovered alpha remain useful across regimes?

### Q5
Is the candidate genuinely novel relative to existing alpha?

### Q6
Does the candidate survive sign reversal and null tests?

### Q7
Does the candidate survive execution assumptions?

### Q8
Does the relationship replicate in an untouched period?

---

# 99. EXAMPLE DISCOVERY FAMILY

Implement a seed family similar to:

```text
GP-MOM-VOL-001
```

Allowed features:

```text
momentum_5
momentum_10
momentum_20
rolling_std_20
rolling_mean_20
```

Allowed operators:

```text
add
sub
mul
safe_div
rank
zscore
abs
rolling_mean
rolling_std
```

Constraints:

```text
max_depth = 4
max_nodes = 15
max_constants = 2
population = 32
generations = 10
```

This is a diagnostic family.

Do not treat it as market evidence.

---

# 100. EXPECTED DISCOVERY OUTPUT

Example conceptual result:

```text
Candidate:
    rank(momentum_20 / rolling_std_20)

Predictive IC:
    0.XX

Complexity:
    5

Redundancy:
    LOW

Novelty:
    MODERATE

Walk-forward:
    PASS

Falsification:
    PASS

Multiple testing:
    BH adjusted

Holdout:
    NOT_TESTED

Execution:
    WARN / NOT_TESTED

Research gate:
    WARN
```

Never invent real-market values.

---

# 101. RESEARCH GATE SEMANTICS

The engine must return something like:

```text
discovery_status
integrity_status
validation_status
multiple_testing_status
replication_status
gate_outcome
```

Example:

```text
discovery_status = DISCOVERY_SURVIVOR
integrity_status = PASS
validation_status = OOS_SURVIVOR
multiple_testing_status = WARN
replication_status = NOT_TESTED
gate_outcome = WARN
```

A discovery survivor is NOT automatically a research candidate.

---

# 102. NOT_TESTED POLICY

Maintain explicit `NOT_TESTED`.

Potential examples:

```text
official_nse_holidays
licensed_nse_dump
nifty_membership
pit_sector
pit_market_cap
calibrated_adv
order_book_depth
institutional_tca
full_cscv_pbo
real_market_replication
```

Never manufacture evidence.

---

# 103. TEST SUITE

Add comprehensive tests under:

```text
tests/discovery/
```

At minimum:

```text
test_expression_ast.py
test_expression_types.py
test_expression_domain.py
test_grammar.py
test_generation.py
test_mutation.py
test_crossover.py
test_genetic_search.py
test_symbolic_search.py
test_complexity.py
test_novelty.py
test_redundancy.py
test_falsification.py
test_walk_forward.py
test_multiple_testing.py
test_lineage.py
test_reproducibility.py
test_budget.py
test_integrity.py
test_snapshot_immutability.py
test_holdout.py
test_null_search.py
test_known_alpha_recovery.py
test_archive.py
test_registry.py
```

Also preserve all existing tests.

---

# 104. QUALITY GATES

Before declaring Prompt 15 complete:

```bash
ruff check .
mypy src/quantlab
pytest
```

All must pass.

No warnings may be hidden.

No tests may be weakened or deleted merely to achieve green status.

---

# 105. REQUIRED VERSION CHECK

After implementation:

```python
import quantlab
assert quantlab.__version__ == "1.5.0"
```

and:

```python
from quantlab.core.safety import LiveSafetyGates

assert LiveSafetyGates().live_trading is False
```

Use the repository's actual safety import path if it differs.

---

# 106. INTEGRATION CHECKLIST

Before completion verify:

- Prompt 01 still works
- Prompt 02 still works
- Prompt 03 desktop still launches
- Prompt 04 PIT fabric still works
- Prompt 05 backtest/validation still works
- Prompt 06 feature/alpha still works
- Prompt 07 portfolio still works
- Prompt 08 factor/risk still works
- Prompt 09 regime still works
- Prompt 10 adaptive learning still works
- Prompt 11 statistical learning still works
- Prompt 12 ensemble still works
- Prompt 13 execution research still works
- Prompt 14 orchestration still works
- Prompt 15 discovery works
- no broker import exists in discovery
- live trading remains false
- no second engine was created

---

# 107. DOCUMENTATION REQUIREMENT

Document the complete scientific lifecycle:

```text
Hypothesis
    ↓
Research Family
    ↓
Grammar
    ↓
Candidate Generation
    ↓
Genetic/Symbolic Search
    ↓
Candidate Evaluation
    ↓
Novelty / Redundancy
    ↓
Falsification
    ↓
Walk-Forward
    ↓
Multiple Testing
    ↓
Confirmation
    ↓
Replication
    ↓
Prompt 05 Gate
    ↓
Ledger
```

Explain why each stage exists.

---

# 108. FINAL DEFINITION OF DONE

Prompt 15 is complete only when QUANT LAB can perform the following end-to-end:

```text
DEFINE HYPOTHESIS
      ↓
CREATE SEARCH FAMILY
      ↓
FREEZE SEARCH SPACE
      ↓
LOAD PIT SNAPSHOT
      ↓
GENERATE CANDIDATES
      ↓
EVOLVE / MUTATE / CROSSOVER
      ↓
EVALUATE
      ↓
TRACK EVERY CANDIDATE
      ↓
FILTER INVALID EXPRESSIONS
      ↓
MEASURE COMPLEXITY
      ↓
MEASURE NOVELTY
      ↓
MEASURE REDUNDANCY
      ↓
FALSIFY
      ↓
WALK-FORWARD VALIDATE
      ↓
ACCOUNT FOR MULTIPLE TESTING
      ↓
PRESERVE HOLDOUT
      ↓
ARCHIVE LINEAGE
      ↓
REPORT
      ↓
SEND TO PROMPT 14 ORCHESTRATION
      ↓
PROMPT 05 GATE
      ↓
LEDGER
```

The system must be capable of saying:

```text
"I searched 1,284 candidates.
17 were unique survivors.
11 were redundant.
23 failed numerical integrity.
8 failed PIT integrity.
6 survived discovery.
4 failed walk-forward.
2 failed multiple-testing controls.
1 survived validation.
Replication is NOT_TESTED.
Therefore this is NOT confirmed alpha."
```

That is the desired behavior.

Not:

```text
"I found the best strategy."
```

---

# 109. FINAL ENGINEERING PRINCIPLE

Build QUANT LAB as a **scientific discovery laboratory**, not a strategy vending machine.

The objective of Prompt 15 is not to maximize the number of profitable-looking formulas.

The objective is to maximize the probability that a surviving mathematical relationship is:

```text
PIT-valid
reproducible
simple enough to understand
statistically defensible
temporally stable
non-redundant
execution-aware
falsification-resistant
independently testable
and honestly classified
```

The engine must aggressively search.

It must aggressively falsify.

It must preserve failures.

It must expose researcher degrees of freedom.

It must never hide the number of candidates tested.

It must never convert synthetic evidence into market evidence.

It must never bypass Prompt 14.

It must never bypass Prompt 05.

It must never place a live order.

**Implement Prompt 15 on the existing QUANT LAB 1.4.0 architecture. Inspect first. Reuse existing infrastructure. Extend, do not duplicate. Test every boundary. Keep the system fail-closed.**
