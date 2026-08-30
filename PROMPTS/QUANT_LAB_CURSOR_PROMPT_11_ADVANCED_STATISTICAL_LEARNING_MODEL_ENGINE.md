# QUANT LAB — CURSOR IMPLEMENTATION PROMPT 11
# Advanced Statistical Learning & Model Research Engine
## Target Version: QUANT LAB 1.1.0
## Engineering Specification — Execute on Existing QUANT LAB 1.0.0

---

# 0. MISSION

You are the principal quantitative researcher, statistical-learning engineer, and safety-critical software architect working inside the existing QUANT LAB repository.

Implement **Prompt 11 — Advanced Statistical Learning & Model Research Engine** on top of the existing QUANT LAB 1.0.0 architecture.

This is an incremental implementation.

**DO NOT reset, rewrite, flatten, fork, or replace the existing architecture.**

First inspect the repository, existing modules, ADRs, tests, CLI, desktop application, experiment ledger, and all previous research contracts.

Preserve Prompts 01–10.

The purpose of this engine is to answer:

> **Does a statistical model extract incremental, persistent, economically meaningful information from PIT-valid features/alphas, beyond simpler baselines, while surviving temporal validation, costs, risk controls, multiple testing, and model-selection bias?**

This is a **research engine**, not an autonomous trading system.

It must never become:

- a stock-picking chatbot;
- a generic ML demo;
- a live trading engine;
- a broker adapter;
- a replacement backtester;
- a replacement PIT data fabric;
- a replacement risk engine;
- a replacement research gate;
- an uncontrolled AutoML system.

---

# 1. EXISTING ARCHITECTURE IS FROZEN

Prompts 01–10 remain authoritative.

The following must remain intact:

```text
PIT Data Fabric
MarketState
StateSnapshot
Feature Engine
Label Engine
Alpha Engine
Portfolio Construction
Factor Engine
Risk Engine
Regime Engine
Adaptive / Online Learning
Backtest Engine
Validation Engine
Research Gate
Experiment Ledger
quantlab.app
Desktop UI
LiveSafetyGates
```

Do not create parallel implementations of these systems.

Especially:

```text
ONE PIT DATA FABRIC
ONE CANONICAL BACKTESTER
ONE RESEARCH GATE
ONE EXPERIMENT LEDGER
ONE RISK FIREWALL
```

---

# 2. CORE SCIENTIFIC SEPARATION

Maintain these distinctions:

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
STRATEGY
  ≠
ORDER
```

A model produces a **research prediction / score / estimate**.

It does not place orders.

---

# 3. PRIMARY RESEARCH QUESTIONS

The engine must make these questions testable:

1. Does the model improve predictive information over a simple alpha?
2. Does nonlinear modeling add incremental information?
3. Does the model outperform a naive baseline OOS?
4. Does regularization improve stability?
5. Does feature selection survive OOS?
6. Does dimensionality reduction improve robustness?
7. Does model complexity improve information or merely fit noise?
8. Are coefficients/features stable through time?
9. Does model performance depend on regime?
10. Does model performance survive realistic costs?
11. Does the model survive perturbation?
12. Does model selection create multiple-testing bias?
13. Does adaptive learning improve the model OOS?
14. Does the model remain calibrated?
15. Does the model degrade under distribution shift?
16. Does the model add information after existing alpha/factor controls?
17. Does the model improve portfolio outcomes after risk and turnover?
18. Does the model survive null, permutation, and leakage tests?

A model that fails is a valid research outcome.

---

# 4. PACKAGE ARCHITECTURE

Inspect existing conventions first.

Prefer a package boundary such as:

```text
src/quantlab/models/
```

Possible modules:

```text
models/
├── __init__.py
├── definitions.py
├── datasets.py
├── targets.py
├── estimators.py
├── linear.py
├── regularized.py
├── nonlinear.py
├── dimensionality.py
├── selection.py
├── calibration.py
├── predictions.py
├── evaluation.py
├── validation.py
├── stability.py
├── importance.py
├── residuals.py
├── baselines.py
├── registry.py
├── cache.py
└── errors.py
```

Do not create unnecessary files merely to satisfy this example.

Use the smallest coherent design consistent with QUANT LAB conventions.

---

# 5. VERSIONED MODEL DEFINITION

Create an immutable, versioned model specification.

Conceptually:

```text
ModelDefinition
```

must identify:

```text
model_id
version
algorithm
features
feature_versions
target
target_version
universe
frequency
training_window
normalization
missing_value_policy
hyperparameters
random_seed
regime_context
adaptive_policy
regularization
selection_method
calibration_method
evaluation_spec
```

The model identity must be deterministic.

Any research-defining change creates a new identity.

Never silently mutate a registered model.

---

# 6. MODEL STATE

Separate immutable model definition from fitted state.

Conceptually:

```text
ModelState
```

should record:

```text
model_definition_id
fit_timestamp
training_start
training_end
available_information_cutoff
parameter_state
feature_schema
training_sample_count
random_seed
software_version
data_snapshot
config_hash
```

The `available_information_cutoff` is mandatory.

A fitted model must be auditable as:

> What exactly could this model know when it was fitted?

---

# 7. TEMPORAL LEARNING CONTRACT

All predictive model evaluation must obey:

```text
TRAIN
  ↓
FREEZE MODEL
  ↓
PREDICT
  ↓
REALIZE OUTCOME
  ↓
UPDATE / REFIT
  ↓
NEXT PREDICTION
```

Never:

```text
FULL DATASET
  ↓
FIT
  ↓
REPLAY HISTORY
```

for predictive performance claims.

Full-sample fitting may exist only as an explicitly labelled descriptive diagnostic.

---

# 8. PIT REQUIREMENT

Every model training observation must satisfy:

```text
available_time <= model_fit_cutoff
```

Every prediction must satisfy:

```text
feature_available_time <= prediction_time
```

Every target must satisfy the existing label semantics.

Never allow:

- future normalization;
- future feature selection;
- future imputation;
- future PCA;
- future target statistics;
- future regime labels;
- future universe membership;
- future covariance;
- future hyperparameter selection.

---

# 9. MODEL DATASET BUILDER

Create a model-ready dataset layer that references existing PIT features and labels.

It must NOT become a second data fabric.

Conceptually:

```text
PIT Feature Store
       +
PIT Label Store
       +
Universe
       +
Temporal Split
       ↓
ModelDataset
```

Each dataset must retain lineage to:

```text
dataset snapshot
feature IDs
feature versions
label ID
universe ID
as-of boundary
frequency
missing policy
normalization policy
```

---

# 10. TARGET / LABEL SAFETY

Models may consume labels only as training targets.

Never allow:

```text
label → feature
```

or:

```text
future label → historical feature
```

The system must detect:

```text
label_as_feature
future_target
future_normalization
future_selection
```

and FAIL integrity.

---

# 11. BASELINE-FIRST DESIGN

Every sophisticated model must have a baseline.

Required baseline hierarchy:

```text
NO-SIGNAL
    ↓
CONSTANT / MEAN
    ↓
EXISTING ALPHA
    ↓
SIMPLE LINEAR MODEL
    ↓
REGULARIZED LINEAR MODEL
    ↓
NONLINEAR MODEL
```

The system must answer:

> What incremental information does the complex model provide over the simplest defensible baseline?

Do not optimize complex models in isolation.

---

# 12. REQUIRED MODEL FAMILY 1 — LINEAR

Implement a strong linear baseline.

Examples:

```text
OLS
Ridge
Lasso
Elastic Net
```

Use regularization where appropriate.

Record:

```text
coefficients
intercept
regularization
feature scaling
sample count
condition diagnostics
```

OLS must not be described as causal inference.

---

# 13. REQUIRED MODEL FAMILY 2 — ROBUST REGRESSION

Where appropriate implement research-grade robust alternatives.

Potential methods:

```text
Huber regression
robust loss
winsorized diagnostic
quantile regression
```

Do not silently transform observations.

Every transformation must be part of the model definition.

---

# 14. REQUIRED MODEL FAMILY 3 — NONLINEAR MODELS

Implement a controlled set rather than an uncontrolled library dump.

Potential first-tier models:

```text
Random Forest
Gradient Boosting
Histogram Gradient Boosting
```

Optionally support:

```text
XGBoost
LightGBM
CatBoost
```

ONLY if dependency policy and environment support them.

Do not make external heavyweight dependencies mandatory unless justified.

The initial engine should work with a minimal local scientific Python stack.

---

# 15. MODEL COMPLEXITY CONTROL

For every nonlinear model record:

```text
depth
number_of_estimators
learning_rate
minimum_leaf_size
feature_fraction / equivalent
regularization
random_seed
```

Complexity must be explicit.

Do not expose hundreds of hyperparameters through the UI.

---

# 16. FEATURE SCALING

Scaling must be fit only on training data.

Examples:

```text
z-score
robust scaling
rank transform
```

Training parameters:

```text
mean
std
median
IQR
```

must never be computed using validation/test/holdout observations.

The fitted transformer is part of `ModelState`.

---

# 17. MISSING VALUE POLICY

Maintain the existing principle:

> Missing information is unavailable information, not zero.

Supported policies may include:

```text
drop
training-only imputation
forward fill only where economically valid
explicit missing indicator
```

Never silently convert missing values to zero.

Record the policy in the model identity.

---

# 18. CROSS-SECTIONAL MODEL SEMANTICS

The engine must support cross-sectional prediction.

At time T:

```text
features_i(T)
      ↓
model
      ↓
score_i(T)
```

The model must not accidentally learn from:

```text
future cross-section
future universe
future ranks
future normalization
```

Cross-sectional transforms must be PIT-valid.

---

# 19. TIME-SERIES MODEL SEMANTICS

Also support time-series research where appropriate.

Explicitly distinguish:

```text
cross-sectional model
vs
per-instrument time-series model
vs
pooled panel model
```

Do not mix these semantics implicitly.

---

# 20. PANEL LEARNING

Where practical, support pooled panel research:

```text
instrument × time
```

with strict temporal separation.

The model must not allow one instrument's future information to leak into another instrument's historical prediction.

---

# 21. FEATURE SELECTION ENGINE

Implement explicit feature-selection methods.

Potential methods:

```text
univariate screening
correlation filtering
mutual information
recursive feature elimination
L1 selection
stability selection
```

Every selection method must operate only inside the training window for predictive evaluation.

Feature selection performed on the full dataset must be marked:

```text
NOT_PREDICTIVE
```

or fail when used in predictive mode.

---

# 22. STABILITY SELECTION

Where practical, implement repeated perturbation/stability analysis.

Evaluate feature inclusion under:

```text
time perturbation
bootstrap-like resampling where statistically appropriate
small parameter perturbations
subperiods
regimes
```

Return:

```text
selection_frequency
stability_score
sample_count
```

Do not interpret feature importance as causal importance.

---

# 23. DIMENSIONALITY REDUCTION

Implement controlled dimensionality-reduction research.

Initial candidate:

```text
PCA
```

Potential future:

```text
Sparse PCA
```

PCA fitting must occur exclusively within the training period.

Record:

```text
components
explained_variance
explained_variance_ratio
fit_window
feature_schema
```

Future data must never affect historical principal components.

---

# 24. FACTOR / FEATURE RESIDUALIZATION

Allow a model to test:

```text
new_alpha
conditional_on
existing_factors
```

Example:

```text
new model
    ↓
control for market beta
    ↓
control for known factor exposures
    ↓
evaluate residual predictive information
```

Do not invent unavailable NIFTY, sector, cap, or ADV data.

Existing `NOT_TESTED` status remains authoritative.

---

# 25. INCREMENTAL INFORMATION TEST

This is a central requirement.

For a candidate model M:

```text
Baseline
vs
Baseline + Candidate Features
```

Measure:

```text
ΔIC
ΔRankIC
Δspread
Δprediction_error
Δportfolio_return
Δrisk
Δturnover
Δcost-adjusted performance
```

The model must not be called "incremental" merely because its standalone score is strong.

---

# 26. MODEL COMPARISON

Implement reproducible comparison.

Compare:

```text
baseline
linear
ridge
lasso
elastic_net
robust
tree
boosting
```

where applicable.

The comparison report must contain:

```text
model
training specification
OOS period
sample size
prediction metric
IC
rank IC
portfolio metric
turnover
cost
risk
stability
statistical evidence
multiple-testing status
integrity status
```

---

# 27. HYPERPARAMETER SEARCH

Implement only controlled search.

Support:

```text
grid
random
```

and optionally a deterministic sequential search.

Every tested configuration must be recorded.

Never allow:

```text
search 10,000 configurations
→ select best
→ report one Sharpe
```

without accounting for selection.

---

# 28. TEMPORAL HYPERPARAMETER SEARCH

Hyperparameters must be selected only using training/validation information.

Correct:

```text
TRAIN
  ↓
candidate hyperparameters
  ↓
VALIDATION
  ↓
freeze hyperparameters
  ↓
HOLDOUT
```

Incorrect:

```text
TRAIN
  ↓
search including holdout
  ↓
choose winner
  ↓
claim OOS
```

Holdout contamination must FAIL integrity.

---

# 29. MODEL SELECTION BIAS

Explicitly account for:

```text
number of models tested
number of hyperparameters
number of feature sets
number of transformations
number of windows
number of regimes
```

Record the research family.

Do not treat the best model among 100 trials as if it were a single hypothesis.

Integrate with Prompt 05 multiple-testing controls.

---

# 30. CROSS-VALIDATION

Temporal model validation must support:

```text
walk-forward
rolling
expanding
anchored
purged
embargoed
```

Use the existing Prompt 05 validation machinery.

Do not create a second independent validation framework if an existing component can be extended.

---

# 31. MODEL CALIBRATION

For probabilistic models, implement calibration diagnostics where applicable.

Potential metrics:

```text
Brier score
log loss
reliability
calibration error
```

Do not apply calibration using future observations.

Calibration transforms must be fit only on permitted historical training/validation data.

---

# 32. PREDICTION OBJECT

Create an explicit immutable prediction object.

Conceptually:

```text
ModelPrediction
```

containing:

```text
model_state_id
instrument/security_id
prediction_time
feature_snapshot
prediction
confidence / uncertainty if available
regime context
```

The prediction must be frozen before outcome realization.

---

# 33. MODEL UNCERTAINTY

Where possible provide uncertainty diagnostics.

For linear models:

```text
standard errors
prediction intervals
```

where statistically appropriate.

For ensembles:

```text
prediction dispersion
```

For bootstrap-like diagnostics:

```text
empirical uncertainty
```

Never manufacture confidence intervals.

If assumptions are not satisfied, report:

```text
NOT_TESTED
```

or an appropriate warning.

---

# 34. MODEL INTERPRETABILITY

Provide controlled diagnostics:

```text
linear coefficients
permutation importance
tree importance
partial dependence
prediction contribution where appropriate
```

Do not describe feature importance as causality.

Interpretability calculations must obey temporal constraints when used for predictive claims.

---

# 35. MODEL STABILITY

Measure stability across:

```text
time
regime
universe subset
feature perturbation
hyperparameter perturbation
random seed
```

Potential outputs:

```text
parameter stability
feature stability
prediction stability
rank stability
performance stability
```

A high-performance model with unstable structure must be flagged.

---

# 36. RESIDUAL ANALYSIS

Implement residual diagnostics where applicable.

Potential diagnostics:

```text
mean residual
variance
autocorrelation
cross-sectional dependence
residual drift
residual regime dependence
```

Do not claim statistical assumptions are satisfied merely because diagnostics run.

---

# 37. MODEL DECAY

Integrate Prompt 10.

For each model measure:

```text
prediction quality over time
rolling IC
rolling error
performance half-life where estimable
degradation
recovery
```

A model can have stable parameters but decaying predictive power.

Treat these as separate concepts.

---

# 38. REGIME-CONDITIONED MODEL PERFORMANCE

Integrate Prompt 09.

Evaluate:

```text
model × regime
```

for:

```text
IC
rank IC
error
spread
turnover
risk
```

Predictive mode must use only PIT-valid filtered regime context.

Smoothed hindsight regimes cannot support predictive claims.

---

# 39. ADAPTIVE MODEL INTEGRATION

Integrate Prompt 10.

The relationship must remain:

```text
Model
  ↓
Adaptive Learner
  ↓
Research Prediction / Weight
```

Do not duplicate adaptive-learning logic.

Use existing `quantlab.adaptive` infrastructure.

---

# 40. MODEL → ALPHA INTEGRATION

A model prediction may become an alpha object only through an explicit conversion.

Maintain:

```text
MODEL ≠ ALPHA
```

The conversion must declare:

```text
source_model_id
prediction_transform
expected_direction
normalization
cross_sectional_policy
```

A model with good predictive accuracy is not automatically a tradable alpha.

---

# 41. PORTFOLIO INTEGRATION

The model output may flow:

```text
Model Prediction
      ↓
Alpha Conversion
      ↓
Portfolio Constructor
      ↓
Risk Engine
      ↓
Existing Backtester
```

The model itself must not know about broker execution.

---

# 42. RISK INTEGRATION

Evaluate model-driven portfolios through Prompt 08.

At minimum:

```text
beta
factor exposure
covariance
volatility
concentration
drawdown
stress
```

Do not bypass risk constraints because a model has high predictive metrics.

---

# 43. COST-AWARE EVALUATION

Use the existing cost schedule.

Default assumptions remain those defined by Prompt 05.

Evaluate:

```text
gross signal effect
turnover
transaction costs
net effect
```

A model that only works before costs must be identified explicitly.

---

# 44. ECONOMIC SIGNIFICANCE

Separate:

```text
statistical significance
from
economic significance
```

Evaluate:

```text
effect size
cost-adjusted effect
turnover
capacity proxy where data exists
risk-adjusted performance
```

Do not invent calibrated ADV.

Capacity remains `NOT_TESTED` where required data is unavailable.

---

# 45. NULL AND PLACEBO TESTS

Mandatory.

Implement:

### Label permutation

Break feature-target temporal relationship.

Expected:

```text
no persistent predictive edge
```

### Feature permutation

Destroy cross-sectional structure.

### Time shift

Shift features relative to labels.

### Random model

Control against arbitrary model complexity.

### Noise features

Add irrelevant features.

### Future feature injection

Must FAIL.

### Future normalization

Must FAIL.

### Future feature selection

Must FAIL.

### Future hyperparameter selection

Must FAIL.

### Holdout contamination

Must FAIL.

---

# 46. COMPLEXITY CONTROL EXPERIMENT

Create a controlled synthetic experiment:

```text
simple true relationship
        ↓
linear
        ↓
regularized linear
        ↓
tree
        ↓
boosting
```

Verify that increased model complexity does not automatically produce superior OOS performance.

The test should demonstrate:

```text
complexity can overfit
```

This is a required architecture validation.

---

# 47. SYNTHETIC MODEL SCENARIOS

Create controlled synthetic scenarios:

```text
linear signal
nonlinear signal
weak signal
zero signal
regime-dependent signal
decaying signal
sign-changing signal
correlated features
redundant features
high-dimensional noise
structural break
```

Use these only to validate implementation behavior.

Synthetic performance is not market evidence.

---

# 48. MODEL REGISTRY

Extend the existing registry architecture.

Support:

```bash
quantlab model list
quantlab model inspect <id>
quantlab model register <id>
quantlab model compare <a> <b>
```

Registry entries must be immutable/versioned.

---

# 49. MODEL EXECUTION CLI

Extend the existing CLI consistently.

Candidate commands:

```bash
quantlab model list

quantlab model inspect <id>

quantlab model fit <id>

quantlab model predict <id>

quantlab model evaluate <id>

quantlab model stability <id>

quantlab model importance <id>

quantlab model residuals <id>

quantlab model compare <a> <b>

quantlab model select <experiment>

quantlab research model <id>

quantlab research model-compare <a> <b>

quantlab research model-stability <id>
```

Use existing CLI architecture.

Do not break:

```text
slice
backtest
validate
research
adaptive
factor
risk
regime
```

---

# 50. DESKTOP INTEGRATION

Extend `quantlab.app` first.

The UI remains a query client.

Add a:

```text
Model Lab
```

with views such as:

```text
Models
Datasets
Predictions
Validation
Model Comparison
Feature Importance
Stability
Residuals
Calibration
Regime Performance
Experiment Lineage
```

The desktop must NOT:

- fit models directly;
- read Parquet directly;
- bypass PIT;
- alter model identities;
- bypass validation;
- bypass risk;
- promote experiments;
- place orders.

---

# 51. COMPUTATIONAL ISOLATION

Follow the existing desktop process-isolation architecture.

Heavy model fitting must not freeze the Qt UI.

Use the existing job/process framework where possible.

Do not introduce an unrelated execution system.

---

# 52. CACHE SAFETY

Cache identity must include:

```text
dataset snapshot
feature IDs
feature versions
label ID
universe
training window
validation window
model definition
hyperparameters
random seed
normalization
selection method
regime context
adaptive context
software version
```

A future data append must not mutate a historical model state.

---

# 53. REPRODUCIBILITY

Every fitted model must be reproducible.

Record:

```text
data snapshot
checksum
model definition
hyperparameters
random seed
feature schema
target
training period
validation period
holdout period
software version
config hash
```

If exact reproducibility cannot be guaranteed due to a dependency/runtime issue, report it explicitly.

---

# 54. EXPERIMENT LEDGER

Every model experiment must create lineage compatible with the existing ledger.

Record:

```text
experiment_id
parent_experiment_id
model_definition_id
dataset_id
dataset_checksum
feature_ids
label_id
universe_id
training_window
validation_window
holdout_window
hyperparameter_search
number_of_candidates
selected_model
metrics
costs
risk
integrity
multiple_testing
gate_result
```

The ledger must retain rejected models too.

Do not record only winners.

---

# 55. MODEL CHAMPION / CHALLENGER

Implement research-only champion/challenger semantics.

Example:

```text
Champion
   vs
Challenger
```

The challenger must be evaluated under the same declared protocol.

Do not silently replace the champion because of one favorable period.

Promotion remains controlled by Prompt 05.

---

# 56. RESEARCH GATE

Prompt 05 remains the **only** research promotion gate.

This module must not invent:

```text
MODEL_PROMOTED
```

as an independent authorization.

A model may receive a research status only through existing gate semantics.

Synthetic experiments cannot become:

```text
RESEARCH_CANDIDATE
```

or:

```text
PROMOTED_TO_PAPER
```

---

# 57. INTEGRITY EXTENSIONS

Add model-specific integrity checks such as:

```text
future_model_training
future_normalization
future_feature_selection
future_pca
future_hyperparameter
future_calibration
holdout_contamination
cross_section_future_leak
model_replay_leak
model_state_mutation
```

Use:

```text
PASS
FAIL
WARN
NOT_TESTED
```

Never turn unknown evidence into PASS.

---

# 58. MULTIPLE TESTING

This is mandatory.

Track:

```text
models tested
features tested
feature subsets tested
hyperparameters tested
windows tested
transformations tested
regime conditions tested
ensemble variants tested
```

Integrate with Prompt 05:

```text
BH
Bonferroni
Holm
DSR where identified
```

Do not manufacture PBO or CSCV results if not implemented.

Keep:

```text
NOT_TESTED
```

honest.

---

# 59. STATISTICAL TESTING

Use appropriate temporal/statistical methods.

Do not assume IID observations.

Where applicable use:

```text
moving-block bootstrap
sign-flip null
permutation controls
robust standard errors
```

Avoid presenting ordinary IID p-values as definitive for autocorrelated financial data.

If a method's assumptions are not implemented/validated, mark it accordingly.

---

# 60. BENCHMARKING

Every model report must compare against:

```text
naive baseline
existing alpha
static model
adaptive model where applicable
```

A model should not be considered useful merely because:

```text
R² > 0
```

or:

```text
accuracy > 50%
```

The benchmark must reflect the actual research objective.

---

# 61. FINANCIAL TARGET METRICS

When predictions are converted to cross-sectional research scores, evaluate:

```text
IC
Rank IC
quantile spread
long-short spread where explicitly defined
hit rate
turnover
cost-adjusted return
drawdown
Sharpe / information ratio where appropriate
```

Keep financial metrics downstream of the prediction engine.

Do not embed portfolio simulation logic inside `quantlab.models`.

---

# 62. MODEL PERFORMANCE DECOMPOSITION

For a model improvement, attempt to attribute the improvement to:

```text
feature information
nonlinearity
regularization
adaptation
regime conditioning
selection
portfolio construction
risk management
```

Do not claim the model caused an improvement if portfolio construction or risk controls are responsible.

---

# 63. NO AUTOMATIC FEATURE IMPORTANCE CLAIMS

Explicitly warn against:

```text
feature importance = causal importance
```

Feature importance is a diagnostic.

Where features are highly correlated, importance can be unstable.

The report must expose:

```text
feature correlation
importance stability
selection stability
```

where available.

---

# 64. DATA SUFFICIENCY

Every model must report:

```text
training sample count
validation sample count
holdout sample count
number of instruments
number of time periods
effective observations
feature dimension
feature/observation ratio
```

Warn about:

```text
high dimensionality
small samples
unstable estimates
class imbalance
missingness
```

Never hide insufficient data.

---

# 65. MODEL FAILURE MODES

Explicitly handle:

```text
insufficient_history
singular_matrix
ill_conditioned_matrix
constant_feature
constant_target
empty_universe
missing_target
missing_features
non_finite_values
unstable_fit
hyperparameter_failure
prediction_failure
future_information
holdout_contamination
```

Use explicit typed exceptions.

Do not silently substitute arbitrary values.

---

# 66. TYPE SAFETY

Maintain:

```text
mypy --strict
ruff
pytest
```

Avoid:

```text
Any
implicit mutable state
global fitted models
silent coercions
hidden randomness
```

All model interfaces should be typed.

---

# 67. DEPENDENCY POLICY

Prefer existing dependencies.

Before adding a new ML library:

1. inspect current environment;
2. determine whether the capability already exists;
3. evaluate maintenance footprint;
4. avoid unnecessary dependency expansion;
5. document the reason.

The core research stack must remain locally executable.

---

# 68. PERFORMANCE

Correctness comes first.

Then optimize:

```text
feature matrix construction
rolling fits
cross-sectional transformations
model caching
repeated experiments
parallel experiment execution
```

Parallel experiments must remain reproducible.

Do not share mutable model state between experiments.

---

# 69. SECURITY / IP

QUANT LAB is local-first.

Do not introduce cloud model training or external data transmission.

Do not upload:

- proprietary datasets;
- experiment results;
- model parameters;
- trading research;
- credentials

to external services.

No API key should be required for the statistical-learning engine.

---

# 70. DOCUMENTATION

Create/update appropriate documentation.

At minimum, following existing naming conventions:

```text
docs/architecture/STATISTICAL_MODEL_ENGINE.md
docs/research/MODEL_RESEARCH.md
docs/research/MODEL_SELECTION.md
docs/research/MODEL_STABILITY.md
docs/research/MODEL_VALIDATION.md
docs/decisions/ADR-025-statistical-learning-model-engine.md
```

Document:

- model taxonomy;
- temporal semantics;
- fitting process;
- validation;
- model-selection bias;
- multiple testing;
- interpretability;
- limitations;
- `NOT_TESTED` items.

---

# 71. ADR-025

Create an architectural decision record establishing:

1. Statistical models are research objects.
2. Existing PIT data remains authoritative.
3. Existing backtester remains authoritative.
4. Model fitting is temporally constrained.
5. Model selection must be recorded.
6. Complex models require baseline comparisons.
7. Multiple testing is mandatory.
8. Adaptive learning remains in Prompt 10.
9. Regime context remains in Prompt 09.
10. Risk remains in Prompt 08.
11. Prompt 05 remains the only research gate.
12. Synthetic data cannot promote.
13. No live execution capability is introduced.

---

# 72. REQUIRED RESEARCH EXPERIMENT 1
## Linear vs Regularized

Build:

```text
existing alpha
      vs
OLS
      vs
Ridge
      vs
Lasso
      vs
Elastic Net
```

Evaluate:

```text
OOS IC
Rank IC
stability
turnover
cost
risk
```

Determine whether regularization improves robustness.

---

# 73. REQUIRED RESEARCH EXPERIMENT 2
## Linear vs Nonlinear

Build:

```text
regularized linear
      vs
Random Forest
      vs
Gradient Boosting
```

Use identical PIT feature/target definitions.

Evaluate under identical temporal validation.

The report must distinguish:

```text
nonlinear information
from
model complexity
```

---

# 74. REQUIRED RESEARCH EXPERIMENT 3
## Feature Selection

Compare:

```text
all features
vs
training-only selected features
```

Test:

```text
stability
OOS performance
feature count
turnover
```

A selection procedure using future data must FAIL.

---

# 75. REQUIRED RESEARCH EXPERIMENT 4
## PCA Leakage

Create:

```text
PCA fitted correctly on training
vs
PCA fitted on full dataset
```

The full-dataset predictive version must be detected as leakage.

This is a mandatory adversarial test.

---

# 76. REQUIRED RESEARCH EXPERIMENT 5
## Complexity Stress Test

Increase model complexity:

```text
low
→
medium
→
high
```

on a zero-alpha synthetic dataset.

Verify that training performance can improve while OOS performance does not necessarily improve.

This validates overfitting controls.

---

# 77. REQUIRED RESEARCH EXPERIMENT 6
## Incremental Alpha

Test:

```text
Existing Alpha
vs
Existing Alpha + Candidate Features
```

Determine whether the candidate model contributes information beyond the existing alpha.

This should become a standard QUANT LAB research workflow.

---

# 78. REQUIRED RESEARCH EXPERIMENT 7
## Regime Conditioning

Evaluate model performance by Prompt 09 state/regime:

```text
model
×
regime
```

Use only predictive regime labels.

Smoothed/full-sample regime context must be rejected for predictive evaluation.

---

# 79. REQUIRED RESEARCH EXPERIMENT 8
## Adaptive Integration

Compare:

```text
Static model
vs
Prompt 10 adaptive model
```

The model engine must not reimplement adaptation.

Measure:

```text
prediction quality
decay
stability
turnover
cost
risk
```

---

# 80. REQUIRED ADVERSARIAL TEST SUITE

Create intentionally broken models for:

```text
future feature
future label
future scaler
future PCA
future feature selection
future hyperparameter
future calibration
future regime
holdout contamination
full-sample model replay
```

Every broken implementation must produce:

```text
FAIL
```

rather than merely:

```text
WARN
```

when the violation is directly detectable.

---

# 81. REQUIRED MODEL LINEAGE

For every prediction, it should be possible to trace:

```text
prediction
 ↓
model state
 ↓
model definition
 ↓
feature definitions
 ↓
PIT dataset
 ↓
data snapshot/checksum
 ↓
training window
 ↓
hyperparameter selection
 ↓
validation
 ↓
research gate
```

This is mandatory for research-grade operation.

---

# 82. UI SAFETY

The desktop UI must never provide a hidden path such as:

```text
Model Lab
→
Run model
→
place trade
```

All model outputs terminate at research/portfolio layers.

Maintain:

```text
LIVE_TRADING=false
```

and existing `LiveSafetyGates`.

---

# 83. NO LLM TRADER

Do not implement:

```text
LLM decides stock
LLM chooses model
LLM selects winner
LLM bypasses gate
LLM requests broker order
```

LLMs may eventually assist research orchestration, but Prompt 11 is a statistical model engine, not an AI-agent system.

---

# 84. ACCEPTANCE CRITERIA

Prompt 11 is complete only when:

## Architecture

- [ ] Existing 0.9/1.0 architecture preserved.
- [ ] No second PIT fabric.
- [ ] No second backtester.
- [ ] No second research gate.
- [ ] No duplicate adaptive engine.
- [ ] Model package integrates cleanly.

## Models

- [ ] Linear baseline.
- [ ] Ridge.
- [ ] Lasso.
- [ ] Elastic Net.
- [ ] Robust model or documented equivalent.
- [ ] Random Forest or equivalent nonlinear baseline.
- [ ] Gradient Boosting or equivalent.
- [ ] PCA.
- [ ] Feature selection.
- [ ] Model comparison.

## Temporal correctness

- [ ] PIT training.
- [ ] PIT prediction.
- [ ] Training-only scaling.
- [ ] Training-only feature selection.
- [ ] Training-only PCA.
- [ ] Temporal hyperparameter selection.
- [ ] Holdout protection.
- [ ] Predict-then-realize semantics.

## Research

- [ ] Baseline comparison.
- [ ] Incremental information testing.
- [ ] Model stability.
- [ ] Feature stability.
- [ ] Residual diagnostics.
- [ ] Model decay.
- [ ] Regime-conditioned analysis.
- [ ] Adaptive comparison.
- [ ] Cost-aware evaluation.

## Statistics

- [ ] Temporal validation.
- [ ] Multiple-testing accounting.
- [ ] Appropriate bootstrap/null controls.
- [ ] No unsupported IID claims.
- [ ] Honest uncertainty.

## Integrity

- [ ] Future feature test fails.
- [ ] Future label test fails.
- [ ] Future normalization test fails.
- [ ] Future PCA test fails.
- [ ] Future feature selection test fails.
- [ ] Future hyperparameter test fails.
- [ ] Future regime test fails.
- [ ] Holdout contamination fails.
- [ ] Full-sample replay fails.

## Integration

- [ ] Prompt 05 works.
- [ ] Prompt 07 works.
- [ ] Prompt 08 works.
- [ ] Prompt 09 works.
- [ ] Prompt 10 works.
- [ ] Desktop works.
- [ ] Existing CLI works.
- [ ] Ledger works.

## Safety

- [ ] `LIVE_TRADING=false`.
- [ ] No broker imports.
- [ ] No live order path.
- [ ] No AI bypass.
- [ ] No external data transmission.

## Quality

- [ ] Full pytest passes.
- [ ] ruff passes.
- [ ] mypy strict passes.
- [ ] Existing regression tests pass.

---

# 85. REQUIRED VALIDATION COMMANDS

Run the repository's canonical commands.

At minimum:

```bash
make test
ruff check .
mypy --strict src
```

Then run model smoke tests using the repository's actual CLI.

For example:

```bash
quantlab model list
quantlab model inspect <known-id>
quantlab model fit <known-id>
quantlab model evaluate <known-id>
quantlab model stability <known-id>
quantlab model compare <a> <b>
quantlab research model <known-id>
```

Also run:

```bash
quantlab slice
quantlab backtest ...
quantlab validate ...
quantlab adaptive ...
```

to verify no regression.

Run desktop offscreen smoke tests if supported.

---

# 86. EXPECTED FINAL IMPLEMENTATION REPORT

When finished, report:

```text
QUANT LAB version
Prompt 11 status
tests passed
ruff status
mypy status
new modules
new model families
new CLI commands
new desktop views
new ADR
new research documents
integrity tests
model comparison results
known NOT_TESTED items
known limitations
live-trading status
```

Also explicitly report:

```text
static baseline
vs
regularized
vs
nonlinear
vs
adaptive
```

and state whether the experiment was:

```text
synthetic
real PIT research
OOS
holdout
```

Do not mix these categories.

---

# 87. FINAL ENGINEERING DIRECTIVE

Think like:

- a quantitative researcher;
- a statistical learning researcher;
- a time-series econometrician;
- a portfolio researcher;
- a software architect;
- a research-audit engineer.

Do not optimize for model sophistication.

Optimize for:

```text
PIT correctness
+
temporal validity
+
incremental information
+
statistical robustness
+
model stability
+
economic significance
+
reproducibility
+
auditability
+
fail-closed safety
```

The correct scientific outcome may be:

```text
SIMPLE MODEL > COMPLEX MODEL
```

or:

```text
NO INCREMENTAL INFORMATION
```

or:

```text
MODEL WORKS ONLY IN-SAMPLE
```

or:

```text
ADAPTATION DOES NOT IMPROVE OOS
```

Those are successful research outcomes.

Do not manufacture positive results.

Do not hide failed models.

Do not select winners without recording the candidate set.

Do not call predictive performance causal.

Do not call statistical significance economic significance.

Do not call synthetic performance alpha.

---

# 88. QUANT LAB RESEARCH PHILOSOPHY

The engine should make the following workflow possible:

```text
HYPOTHESIS
   ↓
FEATURES
   ↓
ALPHA
   ↓
MODEL
   ↓
ADAPTATION
   ↓
REGIME CONDITIONING
   ↓
PORTFOLIO
   ↓
RISK
   ↓
BACKTEST
   ↓
WALK-FORWARD
   ↓
STATISTICAL TESTS
   ↓
MULTIPLE-TESTING CONTROL
   ↓
ROBUSTNESS
   ↓
RESEARCH GATE
   ↓
LEDGER
```

The system should be optimized for **discovering why a hypothesis fails**, not merely for finding a model that fits historical data.

The long-term objective is a computational research laboratory capable of evaluating large numbers of quantitative hypotheses while preserving scientific discipline.

Implement Prompt 11 completely on the existing QUANT LAB codebase.

Do not stop at scaffolding.

Do not fabricate market data.

Do not fabricate performance.

Do not silently weaken validation.

Do not rewrite working architecture.

**Build the smallest genuinely research-grade statistical learning engine that can be defended under adversarial scrutiny and integrated into the existing QUANT LAB research chain.**
