# QUANT LAB — CURSOR IMPLEMENTATION PROMPT 12
# Advanced Ensemble, Meta-Alpha & Model Combination Engine
## Target Version: QUANT LAB 1.2.0

## 0. MISSION

Implement **Prompt 12 — Advanced Ensemble, Meta-Alpha & Model Combination Engine** on top of the existing QUANT LAB 1.1.0 codebase.

This is an incremental implementation. **Do not reset, rewrite, flatten, fork, or replace the existing architecture.**

First inspect the repository, Prompts 01–11, ADRs, tests, CLI, desktop architecture, PIT fabric, learning engine, adaptive engine, factor/risk engine, regime engine, backtester, validation engine, research gate, and experiment ledger.

The research question is:

> **Can multiple imperfect and partially independent predictive sources be combined into a more robust source of information without ensemble-selection, stacking, weighting, or temporal leakage?**

The engine must determine whether an ensemble adds **incremental information beyond its best individual component and beyond a simple equal-weight baseline**.

It must never become an autonomous trading system, second backtester, second PIT fabric, second risk engine, second adaptive engine, or broker execution layer.

---

# 1. EXISTING ARCHITECTURE IS FROZEN

Prompts 01–11 remain authoritative.

Preserve:

```text
PIT Data Fabric
MarketState
StateSnapshot
Feature Engine
Label Engine
Alpha Engine
Portfolio Construction
Factor/Risk Engine
Regime Engine
Adaptive Learning
quantlab.learning
Backtest Engine
Validation Engine
Research Gate
Experiment Ledger
quantlab.app
Desktop UI
LiveSafetyGates
```

There must remain:

```text
ONE PIT DATA FABRIC
ONE CANONICAL BACKTESTER
ONE VALIDATION ENGINE
ONE RISK FIREWALL
ONE RESEARCH GATE
ONE EXPERIMENT LEDGER
```

Extend existing infrastructure rather than duplicating it.

---

# 2. SCIENTIFIC SEPARATION

Maintain:

```text
DATA
≠ FEATURE
≠ FACTOR
≠ ALPHA
≠ REGIME
≠ MODEL
≠ ADAPTIVE LEARNER
≠ ENSEMBLE
≠ META-ALPHA
≠ PORTFOLIO
≠ ORDER
```

Also:

```text
MODEL ≠ ALPHA
ENSEMBLE ≠ PORTFOLIO
META-ALPHA ≠ ORDER
```

An ensemble produces a research-time prediction/score.

It cannot place an order.

---

# 3. PACKAGE

Inspect existing conventions first. Prefer:

```text
src/quantlab/ensemble/
```

Potential modules:

```text
definitions.py
components.py
transforms.py
correlation.py
diversity.py
weighting.py
static.py
dynamic.py
bayesian.py
stacking.py
meta_alpha.py
validation.py
stability.py
diagnostics.py
registry.py
cache.py
errors.py
```

Do not create unnecessary modules. Use the smallest coherent implementation.

---

# 4. VERSIONED ENSEMBLE DEFINITION

Create an immutable, versioned `EnsembleDefinition`.

It must identify:

```text
ensemble_id
version
component_ids
component_versions
component_types
combination_method
normalization
expected_directions
weighting_policy
training_window
validation_window
rebalance_frequency
constraints
regularization
diversity_policy
regime_policy
adaptive_policy
random_seed
```

A formula, component, weighting rule, window, or normalization change must create a new identity.

Never silently mutate a registered ensemble.

---

# 5. COMPONENT CONTRACT

Each component must declare:

```text
component_id
component_type
version
prediction_time
available_information_cutoff
expected_direction
normalization
universe
lineage
```

Supported sources should include, where compatible:

```text
ALPHA
MODEL
ADAPTIVE_MODEL
REGIME_CONDITIONED_MODEL
FACTOR_SIGNAL
```

Reject incompatible or ambiguous components explicitly.

---

# 6. TEMPORAL CONTRACT

All ensemble computation must follow:

```text
COMPONENTS AVAILABLE AT T
        ↓
FREEZE COMPONENT OUTPUTS
        ↓
COMBINE AT T
        ↓
FREEZE ENSEMBLE
        ↓
PREDICT
        ↓
REALIZE T→T+1
        ↓
UPDATE ONLY WHEN PERMITTED
```

Never fit or weight an ensemble using future observations.

---

# 7. PIT CONTRACT

All of these must obey:

```text
available_time <= decision_time
```

including:

```text
component predictions
component IC
component errors
correlations
covariance
volatility
regimes
feature distributions
weights
pruning
hyperparameters
meta-features
```

Future information must produce integrity `FAIL` whenever directly detectable.

---

# 8. NORMALIZATION

Support explicit:

```text
raw
z-score
cross-sectional z-score
rank
rank-zscore
volatility-scaled
```

All normalization must be PIT-valid.

Training/rolling statistics must never include future observations.

Normalization state is part of ensemble identity/state.

---

# 9. DIRECTION

Every component has explicit:

```text
expected_direction = +1 / -1
```

The ensemble must respect it.

Do not flip signs because future performance was poor.

Any sign adaptation must be an explicit Prompt 10-style adaptive policy and must obey its temporal contract.

---

# 10. MANDATORY BASELINES

Every ensemble must be compared with:

```text
Best individual component
Equal-weight ensemble
```

For N components:

```text
w_i = 1/N
```

Sophisticated weighting is not meaningful without these baselines.

---

# 11. REQUIRED WEIGHTING METHODS

Implement controlled versions of:

### Equal Weight

```text
w_i = 1/N
```

### Static historical weighting

Use only training-window information.

### Inverse volatility

```text
w_i ∝ 1/σ_i
```

using PIT historical observations.

### Correlation-aware weighting

Reuse the existing Prompt 08 covariance infrastructure. Do not create another covariance engine.

### Regularized weighting

Support explicit objectives such as:

```text
minimize:
    risk
    - λ × information
    + γ × weight instability
```

All parameters must be versioned.

Hard constraints must raise explicit infeasibility errors. Never silently relax them.

---

# 12. WEIGHT CONSTRAINTS

Support where compatible:

```text
Σw = 1
w_i >= 0
w_i <= max_weight
max_turnover
max_concentration
```

If long-short ensembles are implemented, explicitly distinguish:

```text
Σw
```

from:

```text
Σ|w|
```

and record gross/net exposure.

---

# 13. CORRELATION AND DIVERSITY

Measure PIT-valid:

```text
Pearson correlation
Spearman correlation
rank correlation
prediction correlation
IC correlation
```

where data semantics permit.

Report:

```text
component overlap
prediction disagreement
signal correlation
marginal contribution
effective independence
```

Do not equate low correlation with predictive value.

---

# 14. MARGINAL CONTRIBUTION

For every component, evaluate:

```text
Full ensemble
vs
Ensemble without component
```

Measure:

```text
ΔIC
ΔRankIC
Δspread
Δrisk
Δturnover
Δcost
```

A strong individual component can be redundant.

---

# 15. LEAVE-ONE-OUT

Implement leave-one-out research.

For:

```text
A+B+C+D
```

evaluate:

```text
A+B+C
A+B+D
A+C+D
B+C+D
```

where computationally feasible.

Record all results, not only the winner.

---

# 16. META-ALPHA

Create a distinct `MetaAlpha` research object.

Conceptually:

```text
component scores
+
historical PIT component behavior
        ↓
meta-model
        ↓
composite score
```

Maintain:

```text
META-ALPHA ≠ ALPHA
```

Preserve complete component lineage.

---

# 17. LINEAR META-ALPHA

Reuse Prompt 11 learning infrastructure.

Support:

```text
OLS
Ridge
Elastic Net
```

where appropriate.

Do not create another model framework.

Weights must be fitted only on valid historical windows.

---

# 18. RANK META-ALPHA

Support simple:

```text
rank(A) + rank(B) + ...
```

with explicit normalization.

This is a baseline, not proof of alpha.

---

# 19. STACKING

Implement controlled stacking:

```text
BASE MODELS
   ↓
WALK-FORWARD / OUT-OF-SAMPLE PREDICTIONS
   ↓
META TRAINING MATRIX
   ↓
META MODEL
   ↓
FINAL SCORE
```

The meta-model must never train on in-sample base predictions when those predictions are being used for predictive evidence.

---

# 20. STACKING LEAKAGE TEST

Mandatory adversarial test.

Incorrect:

```text
fit base model
→ predict same training observations
→ train meta-model
```

must produce:

```text
stacking_leak = FAIL
```

Correct construction must use temporally valid out-of-sample predictions.

---

# 21. NESTED VALIDATION

When selecting:

```text
components
weights
hyperparameters
normalization
pruning
meta-model
```

use:

```text
Outer train
  ↓
Inner train/validation
  ↓
select/freeze
  ↓
Outer test
```

The final holdout remains untouched.

---

# 22. DYNAMIC ENSEMBLES

Support research-only dynamic weighting using PIT evidence such as:

```text
rolling IC
rolling RankIC
rolling error
component volatility
component correlation
regime context
```

Weights must be recorded at each decision time.

No future information.

---

# 23. WEIGHT TURNOVER

Use the existing convention where applicable:

```text
0.5 × L1(weight_t - weight_t-1)
```

Record:

```text
weight_turnover
component_turnover
ensemble_turnover
```

A gross improvement caused by excessive weight churn must be exposed.

---

# 24. WEIGHT STABILITY

Measure:

```text
weight variance
weight autocorrelation
sign stability
rank stability
maximum weight change
```

Optional temporal smoothing must be explicit and versioned.

---

# 25. BAYESIAN / MODEL AVERAGING

Where feasible implement a lightweight model-averaging method based only on historical evidence.

Do not add a heavyweight probabilistic dependency unnecessarily.

If rigorous posterior uncertainty is unavailable, report:

```text
NOT_TESTED
```

Do not manufacture posterior probabilities.

---

# 26. REGIME-CONDITIONED ENSEMBLES

Integrate Prompt 09.

Possible architecture:

```text
PIT regime
   ↓
component selection / weighting
```

Predictive regime context only.

Smoothed hindsight HMM or full-sample clustering must not support predictive ensemble selection.

---

# 27. ADAPTIVE ENSEMBLES

Integrate Prompt 10.

Do not duplicate adaptive logic.

Use the existing adaptive infrastructure for:

```text
rolling efficacy
decay
drift
dynamic weighting evidence
```

---

# 28. HETEROGENEOUS COMPONENTS

Support combinations such as:

```text
momentum alpha
mean-reversion alpha
OLS model
Ridge model
adaptive model
regime-conditioned model
factor signal
```

All components must retain independent identity and lineage.

---

# 29. REDUNDANCY

Detect redundant components.

Example:

```text
momentum_20
momentum_21
momentum_22
```

may be highly correlated.

Report:

```text
HIGH_REDUNDANCY
```

but do not silently remove them.

---

# 30. PRUNING

If pruning is implemented, make it explicit:

```text
correlation threshold
marginal contribution threshold
stability threshold
```

Every pruning decision must be logged.

Future full-sample correlation cannot be used for predictive historical decisions.

---

# 31. META-FEATURES

Permitted meta-features may include:

```text
component scores
component ranks
component disagreement
rolling PIT IC
rolling PIT error
component volatility
component correlation
predictive regime
```

Every meta-feature needs an `available_time`.

---

# 32. FORBIDDEN META-FEATURES

These must fail in predictive mode:

```text
future component IC
future ensemble Sharpe
future component ranking
future correlation
future covariance
future regime
future portfolio return
future drawdown
future weight performance
```

---

# 33. COMPONENT PERFORMANCE MATRIX

Create a research matrix:

```text
time × component
```

containing where applicable:

```text
prediction
realized label
IC contribution
rank
error
regime
weight
```

Construct chronologically.

---

# 34. ENSEMBLE ATTRIBUTION

Where mathematically meaningful, calculate:

```text
component contribution
weight contribution
interaction contribution
```

Do not make causal claims from non-identifiable decompositions.

---

# 35. EVALUATION

Every ensemble report must contain:

```text
best individual
equal weight
candidate ensemble
```

and, where implemented:

```text
static
correlation-aware
dynamic
meta-alpha
stacking
```

Metrics:

```text
IC
RankIC
quantile spread
hit rate
turnover
cost
volatility
drawdown
Sharpe / information ratio where appropriate
```

Portfolio metrics must come from the existing backtester.

---

# 36. COST AWARENESS

Use existing Prompt 05 cost schedules.

Report:

```text
gross information/performance
turnover
transaction cost
net information/performance
```

Zero-cost experiments must not be represented as realistic execution evidence.

---

# 37. PORTFOLIO INTEGRATION

Correct chain:

```text
Components
   ↓
Ensemble
   ↓
Meta-Alpha
   ↓
Portfolio Constructor
   ↓
Risk Engine
   ↓
Existing Backtester
   ↓
Validation
   ↓
Research Gate
```

Never:

```text
Ensemble → Broker
```

---

# 38. RISK INTEGRATION

Use Prompt 08 for:

```text
beta
factor exposure
covariance
concentration
volatility
drawdown
stress
```

Do not bypass portfolio constraints.

Do not invent NIFTY, ADV, sector, market-cap, or capacity data.

---

# 39. MULTIPLE TESTING

Ensemble research creates severe selection bias.

Track:

```text
number of components
number of combinations
number of weighting methods
number of normalization methods
number of windows
number of regimes
number of pruning rules
number of meta-models
number of hyperparameter configurations
number of ensemble variants
```

Integrate Prompt 05:

```text
BH
Bonferroni
Holm
DSR where identified
```

Do not manufacture PBO/CSCV.

Keep unsupported methods:

```text
NOT_TESTED
```

---

# 40. ENSEMBLE OVERFITTING

Mandatory synthetic experiment.

Create random/noise components.

Search many combinations.

Verify:

```text
best in-sample ensemble
≠ necessarily best OOS ensemble
```

Selection bias must be visible.

---

# 41. DIVERSITY EXPERIMENT

Create:

```text
strong + highly correlated components
weak + independent components
```

Verify that the engine distinguishes:

```text
diversity
from
predictive value
```

---

# 42. STACKING EXPERIMENT

Compare:

```text
equal weight
Ridge stacking
Elastic-Net stacking
```

using strict walk-forward out-of-sample base predictions.

---

# 43. DYNAMIC WEIGHT EXPERIMENT

Compare:

```text
equal
static
rolling IC
EWMA IC
```

under:

```text
stable signal
decaying signal
regime-switching signal
zero-alpha
```

Synthetic results are architecture diagnostics only.

---

# 44. META-ALPHA INCREMENTAL TEST

Compare:

```text
best component
vs
equal ensemble
vs
meta-alpha
```

Answer:

> Does the meta-alpha contain information beyond the individual components?

---

# 45. REGIME EXPERIMENT

Evaluate:

```text
ensemble × regime
```

using only predictive regime labels.

---

# 46. ADAPTIVE EXPERIMENT

Compare:

```text
static ensemble
vs
Prompt 10 adaptive ensemble
```

without reimplementing adaptive learning.

---

# 47. ADVERSARIAL LEAKAGE TESTS

Implement tests for:

```text
future_component_performance
future_ensemble_weight
future_correlation
future_covariance
future_normalization
future_meta_feature
future_regime
future_component_selection
future_stacking_prediction
future_hyperparameter
future_pruning
future_calibration
holdout_contamination
full_sample_ensemble_replay
model_state_mutation
```

Directly detectable violations must return:

```text
FAIL
```

---

# 48. HISTORICAL IMMUTABILITY

Append future data to the PIT dataset and recompute historical results.

Historical:

```text
component predictions
weights
ensemble scores
```

must remain unchanged.

Otherwise:

```text
model_state_mutation = FAIL
```

---

# 49. ENSEMBLE STATE

Create an immutable `EnsembleState` containing:

```text
ensemble_definition_id
fit_timestamp
training_start
training_end
available_information_cutoff
component_states
weights
weight_policy
normalization_state
correlation_state
hyperparameters
random_seed
dataset_snapshot
config_hash
```

---

# 50. ENSEMBLE PREDICTION

Create an explicit immutable `EnsemblePrediction` containing:

```text
ensemble_state_id
prediction_time
security_id
component_predictions
component_weights
composite_score
normalization
regime_context
available_information_cutoff
```

---

# 51. REPRODUCIBILITY

Every ensemble must be reproducible from:

```text
dataset checksum
component versions
component states
ensemble definition
weight policy
normalization
training window
validation window
holdout window
random seed
software version
config hash
```

---

# 52. EXPERIMENT LEDGER

Extend the existing ledger with:

```text
experiment_id
parent_experiment_id
ensemble_id
component_ids
component_versions
dataset_id
dataset_checksum
training_window
validation_window
holdout_window
combination_method
weighting_policy
candidate_count
evaluated_count
selected_variant
metrics
costs
risk
diversity
stability
multiple_testing
integrity
gate_outcome
```

Retain rejected candidates.

Never log only the winner.

---

# 53. CHAMPION / CHALLENGER

Support research-only:

```text
Champion Ensemble
vs
Challenger Ensemble
```

under identical declared protocols.

Do not replace a champion solely because of higher historical Sharpe.

---

# 54. COMPUTATIONAL CONTROLS

Prevent combinatorial explosion with explicit:

```text
max_components
max_combinations
max_trials
deterministic random seeds
```

If search is truncated:

```text
search_truncated = WARN
```

Do not claim exhaustive search.

---

# 55. SEARCH ACCOUNTING

For every search record:

```text
candidate_count
evaluated_count
pruned_count
failed_count
selection_rule
```

These counts feed multiple-testing analysis.

---

# 56. CACHE SAFETY

Cache keys must include:

```text
dataset snapshot
component versions
component states
ensemble definition
weighting policy
normalization
training window
validation window
regime policy
adaptive policy
random seed
software version
```

Future data must never mutate historical cache results.

---

# 57. CLI

Extend the existing CLI.

Implement appropriate commands such as:

```bash
quantlab ensemble list
quantlab ensemble inspect <id>
quantlab ensemble build <id>
quantlab ensemble fit <id>
quantlab ensemble predict <id>
quantlab ensemble evaluate <id>
quantlab ensemble weights <id>
quantlab ensemble correlation <id>
quantlab ensemble diversity <id>
quantlab ensemble attribution <id>
quantlab ensemble stability <id>
quantlab ensemble leave-one-out <id>
quantlab ensemble compare <a> <b>
quantlab ensemble select <experiment>

quantlab research ensemble <id>
quantlab research ensemble-compare <a> <b>
quantlab research ensemble-diversity <id>
quantlab research meta-alpha <id>
quantlab research stacking <id>
quantlab research ensemble-stability <id>
```

Preserve all existing commands.

---

# 58. DESKTOP

Extend `quantlab.app` first.

Add:

```text
Ensemble Lab
```

Possible views:

```text
Ensemble Registry
Component Matrix
Correlation
Diversity
Weights
Meta-Alpha
Stacking
Leave-One-Out
Stability
Regime Analysis
Attribution
Validation
Experiment Lineage
```

UI is a query/view layer.

It must NOT:

- fit ensembles directly;
- read Parquet directly;
- bypass PIT;
- alter model state;
- bypass validation;
- bypass risk;
- bypass the research gate;
- place orders.

---

# 59. COMPUTATIONAL ISOLATION

Heavy ensemble searches must not freeze the Qt application.

Reuse the existing job/process architecture.

Do not create an unrelated execution system.

---

# 60. SAFETY

Maintain:

```text
LIVE_TRADING=false
```

and existing `LiveSafetyGates`.

The ensemble package must not import:

```text
Zerodha
OpenAlgo
broker APIs
```

and must never produce live orders.

---

# 61. AI BOUNDARY

Do not implement an autonomous AI ensemble trader.

No LLM may:

```text
choose a winning ensemble
bypass validation
override the research gate
request live orders
```

AI research orchestration, if introduced later, remains subordinate to deterministic controls.

---

# 62. RESEARCH GATE

Prompt 05 remains the only promotion authority.

Do not create a competing ensemble gate.

Statuses remain compatible with the existing system:

```text
REJECT
WARN
RESEARCH_CANDIDATE
PROMOTED_TO_PAPER
```

Synthetic data cannot promote.

Integrity FAIL cannot produce a successful research result.

---

# 63. REQUIRED BASELINE MATRIX

Every ensemble report must include:

```text
Best Individual Component
Equal Weight
Static Weight
Correlation-Aware Weight
Dynamic Weight
Meta-Alpha
Stacking
```

where implemented.

---

# 64. REQUIRED METRICS

Information layer:

```text
IC
RankIC
IC stability
IC decay
quantile spread
component correlation
prediction correlation
marginal contribution
```

Portfolio layer:

```text
return
volatility
Sharpe / information ratio
drawdown
turnover
cost
risk exposures
```

Research layer:

```text
sample count
candidate count
multiple-testing status
integrity
stability
gate outcome
```

---

# 65. NO SHARPE OPTIMIZATION TRAP

Do not optimize weights solely for historical Sharpe unless explicitly declared.

If Sharpe optimization is tested, account for:

```text
selection bias
multiple testing
temporal validation
holdout protection
```

---

# 66. NULL ENSEMBLE TEST

Create random/noise components.

Construct many ensembles.

Verify that the best-looking historical ensemble does not receive false promotion.

The result should expose:

```text
selection bias
```

rather than manufacture alpha.

---

# 67. CORRELATED ALPHA TEST

Create:

```text
Alpha A
Alpha B ≈ Alpha A
Alpha C independent
```

Verify:

```text
A+B
```

does not automatically contain twice the information of A.

Also test whether:

```text
A+C
```

can provide incremental information when C is independently informative.

---

# 68. SIGN REVERSAL TEST

Create a component whose apparent historical performance changes sign.

Verify:

```text
ensemble does not automatically reverse direction
```

unless an explicit valid adaptive policy allows it.

---

# 69. FUTURE WEIGHT TEST

Deliberately calculate weights from future returns.

Expected:

```text
future_ensemble_weight = FAIL
```

---

# 70. FUTURE CORRELATION TEST

Deliberately calculate correlation using future observations.

Expected:

```text
future_correlation = FAIL
```

---

# 71. STACKING LEAK TEST

Train a meta-model using in-sample base predictions.

Expected:

```text
stacking_leak = FAIL
```

---

# 72. HOLDOUT SEARCH TEST

Search ensemble variants using holdout observations.

Expected:

```text
holdout_contamination = FAIL
```

---

# 73. HISTORICAL IMMUTABILITY TEST

Append future observations.

Expected:

```text
historical component predictions unchanged
historical weights unchanged
historical ensemble scores unchanged
```

Otherwise:

```text
model_state_mutation = FAIL
```

---

# 74. DOCUMENTATION

Create/update:

```text
docs/architecture/ENSEMBLE_ENGINE.md
docs/research/ENSEMBLE_RESEARCH.md
docs/research/META_ALPHA.md
docs/research/ENSEMBLE_SELECTION.md
docs/research/STACKING.md
docs/research/ENSEMBLE_DIVERSITY.md
docs/research/ENSEMBLE_STABILITY.md
docs/decisions/ADR-026-advanced-ensemble-meta-alpha.md
```

Document architecture, temporal semantics, weighting, stacking, diversity, selection bias, multiple testing, limitations, and NOT_TESTED status.

---

# 75. ADR-026

The ADR must establish:

1. Ensembles are research objects.
2. Meta-alpha is distinct from alpha.
3. Components remain independently versioned.
4. PIT is mandatory.
5. Prompt 11 learning infrastructure is reused.
6. Prompt 08 covariance/risk infrastructure is reused.
7. Stacking requires temporally valid out-of-sample base predictions.
8. Ensemble selection is subject to multiple-testing controls.
9. Equal-weight is mandatory baseline.
10. Marginal contribution is mandatory.
11. Dynamic weights require PIT evidence.
12. Prompt 05 remains the sole research gate.
13. Synthetic results cannot promote.
14. No broker integration.
15. `LIVE_TRADING=false`.

---

# 76. REQUIRED EXPERIMENTS

Implement at least:

### Experiment A — Equal vs Static
```text
best component
vs equal weight
vs static historical weighting
```

### Experiment B — Correlation-Aware
```text
equal
vs performance weight
vs correlation-aware
```

### Experiment C — Leave-One-Out
```text
full
vs each component removed
```

### Experiment D — Stacking
```text
equal
vs Ridge stack
vs Elastic-Net stack
```

with walk-forward OOS base predictions.

### Experiment E — Dynamic Weighting
```text
static
vs rolling IC
vs EWMA IC
```

### Experiment F — Ensemble Overfitting
Search many random/noise combinations.

### Experiment G — Meta-Alpha
```text
best component
vs equal ensemble
vs meta-alpha
```

### Experiment H — Regime Conditioning
```text
ensemble × predictive regime
```

### Experiment I — Adaptive Integration
```text
static ensemble
vs Prompt 10 adaptive ensemble
```

### Experiment J — Historical Immutability
Append future data and verify historical outputs remain identical.

---

# 77. TEST REQUIREMENTS

Add comprehensive tests covering:

```text
definition identity
component validation
normalization
direction
equal weights
static weights
correlation-aware weights
weight constraints
weight turnover
diversity
leave-one-out
meta-alpha
stacking
walk-forward stacking
dynamic weighting
regime integration
adaptive integration
multiple testing
ledger lineage
cache identity
historical immutability
future leakage
holdout contamination
synthetic nulls
desktop offscreen integration
CLI integration
```

Run the complete regression suite from Prompts 01–11.

---

# 78. TYPE / CODE QUALITY

Maintain:

```bash
ruff check .
mypy --strict src
pytest
```

Avoid:

```text
Any
global mutable model state
hidden randomness
silent coercion
silent constraint relaxation
implicit future data
```

---

# 79. DEPENDENCY POLICY

Reuse existing dependencies.

Do not introduce heavyweight ML/probabilistic libraries unless necessary.

Before adding one:

1. inspect current dependencies;
2. determine whether existing infrastructure can provide the capability;
3. justify the dependency;
4. document it;
5. preserve local reproducibility.

---

# 80. FAILURE MODES

Explicitly handle:

```text
empty_components
duplicate_components
incompatible_universes
incompatible_frequencies
direction_conflict
missing_predictions
non_finite_predictions
insufficient_history
singular_weight_problem
infeasible_constraints
future_information
future_weighting
future_correlation
future_selection
stacking_leak
holdout_contamination
model_state_mutation
search_limit_exceeded
```

Use typed exceptions.

Never silently repair a scientifically invalid experiment.

---

# 81. FINAL ACCEPTANCE CRITERIA

Prompt 12 is complete only when:

## Architecture
- [ ] Existing 1.1 architecture preserved.
- [ ] No second PIT fabric.
- [ ] No second backtester.
- [ ] No second covariance engine.
- [ ] No second adaptive engine.
- [ ] No second research gate.
- [ ] Existing ledger extended, not replaced.

## Ensemble
- [ ] Versioned ensemble definition.
- [ ] Immutable ensemble state.
- [ ] Immutable ensemble prediction.
- [ ] Component lineage.
- [ ] Equal-weight baseline.
- [ ] Static weighting.
- [ ] Correlation-aware weighting.
- [ ] Dynamic weighting.
- [ ] Meta-alpha.
- [ ] Controlled stacking.
- [ ] Leave-one-out analysis.
- [ ] Diversity diagnostics.
- [ ] Stability diagnostics.

## Temporal correctness
- [ ] PIT component inputs.
- [ ] PIT weighting.
- [ ] PIT correlation.
- [ ] PIT covariance.
- [ ] PIT normalization.
- [ ] PIT meta-features.
- [ ] Walk-forward stacking.
- [ ] Holdout protection.
- [ ] Predict → realize semantics.

## Statistical research
- [ ] Incremental information.
- [ ] Baseline comparison.
- [ ] Multiple-testing accounting.
- [ ] Null ensemble tests.
- [ ] Selection-bias diagnostics.
- [ ] Model/ensemble stability.
- [ ] Regime-conditioned research.
- [ ] Adaptive integration.

## Integration
- [ ] Prompt 05 gate.
- [ ] Prompt 07 portfolio.
- [ ] Prompt 08 risk.
- [ ] Prompt 09 regime.
- [ ] Prompt 10 adaptive.
- [ ] Prompt 11 learning.
- [ ] Existing backtester.
- [ ] Existing ledger.
- [ ] Desktop Ensemble Lab.
- [ ] CLI.

## Safety
- [ ] `LIVE_TRADING=false`.
- [ ] No broker imports.
- [ ] No order generation.
- [ ] No AI gate bypass.
- [ ] No external data transmission.

## Quality
- [ ] Full pytest passes.
- [ ] ruff passes.
- [ ] mypy strict passes.
- [ ] Existing regression tests pass.
- [ ] UI offscreen tests pass.

---

# 82. REQUIRED FINAL REPORT

Report:

```text
QUANT LAB version
Prompt 12 status
tests passed
ruff
mypy
new modules
new CLI commands
new desktop views
ADR created
research documentation
ensemble methods
stacking implementation
dynamic weighting
diversity diagnostics
leave-one-out results
multiple-testing accounting
adversarial leakage tests
known NOT_TESTED items
known limitations
live-trading status
```

Also compare:

```text
Best Component
vs
Equal Weight
vs
Static Weight
vs
Correlation-Aware
vs
Dynamic
vs
Meta-Alpha
vs
Stacking
```

Do not report only the winner.

---

# 83. FINAL ENGINEERING DIRECTIVE

Think like a researcher trying to **disprove the ensemble before accepting it**.

The engine must make it easy to discover:

```text
ensemble adds no information
ensemble improvement disappears OOS
dynamic weighting overfits
stacking leakage created the apparent edge
components are redundant
diversity improves robustness but not return
one component dominates
selection bias explains the result
```

These are successful research outcomes.

Do not manufacture a superior ensemble.

Do not hide failed candidates.

Do not select winners without recording the candidate set.

Do not call synthetic performance alpha.

Do not call statistical significance economic significance.

Do not call correlation diversity predictive information.

---

# 84. QUANT LAB ENSEMBLE RESEARCH LOOP

The intended research chain is:

```text
HYPOTHESIS
    ↓
FEATURES
    ↓
ALPHAS / MODELS
    ↓
COMPONENT LIBRARY
    ↓
COMPONENT VALIDATION
    ↓
CORRELATION / DIVERSITY
    ↓
ENSEMBLE
    ↓
META-ALPHA
    ↓
WALK-FORWARD VALIDATION
    ↓
MULTIPLE-TESTING CONTROL
    ↓
ROBUSTNESS
    ↓
REGIME ANALYSIS
    ↓
ADAPTIVE ANALYSIS
    ↓
PORTFOLIO
    ↓
RISK
    ↓
EXISTING BACKTESTER
    ↓
RESEARCH GATE
    ↓
EXPERIMENT LEDGER
```

The objective is not:

```text
find the best combination
```

It is:

> **Determine whether combining independent sources of information produces a statistically and economically defensible improvement that survives temporal validation, model-selection bias, realistic costs, risk controls, and adversarial leakage testing.**

---

# 85. NON-NEGOTIABLE RULES

```text
DO NOT RESET THE REPOSITORY.
DO NOT REWRITE PROMPTS 01–11.
DO NOT CREATE A SECOND BACKTESTER.
DO NOT CREATE A SECOND PIT FABRIC.
DO NOT CREATE A SECOND RISK ENGINE.
DO NOT CREATE A SECOND ADAPTIVE ENGINE.
DO NOT BYPASS PROMPT 05.
DO NOT USE FUTURE COMPONENT PERFORMANCE.
DO NOT USE FUTURE CORRELATION.
DO NOT USE FUTURE WEIGHTS.
DO NOT TRAIN STACKING ON IN-SAMPLE BASE PREDICTIONS.
DO NOT SEARCH THE HOLDOUT.
DO NOT HIDE FAILED ENSEMBLES.
DO NOT REPORT ONLY THE WINNER.
DO NOT INVENT MARKET DATA.
DO NOT FABRICATE CAPACITY.
DO NOT CALL SYNTHETIC RESULTS ALPHA.
DO NOT ADD LIVE TRADING.
DO NOT ADD BROKER EXECUTION.
DO NOT LET AI OVERRIDE SAFETY.
DO NOT SILENTLY RELAX CONSTRAINTS.
DO NOT TURN NOT_TESTED INTO PASS.
```

**Implement Prompt 12 completely on the existing QUANT LAB 1.1.0 codebase.**

Build the smallest genuinely research-grade ensemble/meta-alpha engine that can withstand adversarial quantitative scrutiny and integrate cleanly into the existing QUANT LAB research chain.
