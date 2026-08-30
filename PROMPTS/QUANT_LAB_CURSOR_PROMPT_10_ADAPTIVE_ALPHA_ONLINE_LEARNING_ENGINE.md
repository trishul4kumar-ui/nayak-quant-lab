# QUANT LAB — CURSOR IMPLEMENTATION PROMPT 10
# Adaptive Alpha & Online Learning Engine
## Version Target: QUANT LAB 1.0.0
## Status: ENGINEERING SPECIFICATION — EXECUTE ON EXISTING TREE

---

## 0. ROLE

You are the principal quantitative-software architect and research engineer working inside the existing QUANT LAB repository.

Implement **Prompt 10 — Adaptive Alpha & Online Learning Engine** on top of the existing QUANT LAB 0.9.0 architecture.

This is an incremental engineering task.

**DO NOT reset, rewrite, flatten, fork, or replace the existing architecture.**

You must inspect the current repository first and preserve all functionality from Prompts 01–09.

The objective is to create a research-grade framework for answering:

> **Does an alpha remain useful as the information distribution, market state, regime, and alpha efficacy evolve through time, and can we adapt research parameters without introducing hindsight, leakage, unstable model behavior, or hidden multiple testing?**

This subsystem is for **research and controlled backtesting**.

It is NOT:

- an autonomous trading agent;
- a live trading engine;
- an LLM stock picker;
- a broker;
- a replacement for the backtester;
- a replacement for the PIT data fabric;
- a replacement for the Prompt 05 research gate;
- a permission to trade live.

---

# 1. NON-NEGOTIABLE ARCHITECTURAL PRINCIPLES

These are hard requirements.

### 1.1 Preserve Prompts 01–09

Do not break or duplicate:

- PIT Data Fabric
- `MarketState`
- `StateSnapshot`
- feature engine
- label engine
- alpha engine
- cross-sectional portfolio construction
- factor engine
- risk engine
- regime/state engine
- existing backtester
- validation engine
- research gate
- experiment ledger
- desktop application architecture
- `quantlab.app`
- safety firewall

The existing backtester remains the **single source of truth for portfolio simulation**.

Do not create a second backtester.

---

# 2. CORE SCIENTIFIC SEPARATION

Maintain these distinctions throughout the implementation:

```text
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
ONLINE LEARNER
    ≠
PORTFOLIO
    ≠
STRATEGY
    ≠
ORDER
```

In particular:

```text
Adaptive learner
    → may produce a research-time alpha score / parameter estimate / ensemble weight
    → may NOT directly create a broker order
```

The learner must output research objects that downstream portfolio construction and risk systems consume.

---

# 3. PRIMARY RESEARCH QUESTIONS

The implementation must allow QUANT LAB to investigate:

1. Does alpha efficacy decay?
2. What is the alpha half-life?
3. Does alpha efficacy vary by regime?
4. Does a rolling learner outperform a static learner OOS?
5. Does exponential weighting improve adaptation?
6. When does an alpha become stale?
7. Does dynamic ensemble weighting improve robustness?
8. Is adaptation actually useful, or merely overfitting?
9. Does online adaptation survive walk-forward evaluation?
10. Does concept drift explain model degradation?
11. How sensitive are results to adaptation speed?
12. Does adaptive parameter selection create hidden multiple testing?
13. Does the learner remain stable during regime transitions?
14. Does a model improve risk-adjusted performance after realistic costs?
15. Does adaptation survive null/permutation controls?
16. Can the apparent improvement be explained by turnover or leverage?
17. Does the adaptive system outperform a properly constructed static baseline?

A positive result is NOT automatically alpha.

A negative result is a valid research result.

---

# 4. ARCHITECTURE

Create a clean package boundary, preferably:

```text
src/quantlab/adaptive/
```

with appropriate modules such as:

```text
adaptive/
├── __init__.py
├── definitions.py
├── state.py
├── observations.py
├── learners.py
├── rolling.py
├── ewma.py
├── online.py
├── bayesian.py
├── ensembles.py
├── weighting.py
├── decay.py
├── drift.py
├── stability.py
├── evaluation.py
├── prequential.py
├── baselines.py
├── selection.py
├── registry.py
├── cache.py
└── errors.py
```

Do not blindly create every file.

First inspect the existing package conventions and use the smallest coherent module structure.

---

# 5. ADAPTIVE RESEARCH OBJECT MODEL

Introduce explicit immutable/versioned identities.

At minimum implement concepts equivalent to:

```text
AdaptiveModelDefinition
AdaptiveModelState
OnlineObservation
UpdateEvent
AdaptiveParameter
AdaptiveEnsemble
AlphaWeightState
DriftState
DecayEstimate
StabilityReport
PrequentialResult
AdaptiveExperiment
```

Every research object must have deterministic identity.

Identity should include relevant fields such as:

```text
definition_id
version
formula / algorithm identity
training window
update frequency
decay parameter
learning parameters
feature identities
alpha identities
regime conditioning
universe identity
data snapshot
normalization policy
cost assumptions
evaluation specification
random seed
```

Changing any research-defining property must create a new identity.

Never silently overwrite a prior experiment.

---

# 6. POINT-IN-TIME SAFETY

This is the highest-priority requirement.

Every adaptive update must obey:

```text
information_available_at_update_time
    <=
decision_time
```

An observation that becomes available after T cannot affect model state at T.

Do not use:

- future returns;
- future features;
- future labels;
- future universe membership;
- future corporate actions;
- future regime labels;
- future normalization statistics;
- future volatility estimates;
- future covariance;
- future ensemble performance.

unless the research specification explicitly defines a historical availability time and the PIT fabric confirms it.

---

# 7. ONLINE UPDATE SEMANTICS

Define an explicit update protocol.

Conceptually:

```text
At decision time T:

1. Load PIT state available at T.
2. Obtain features known at T.
3. Produce prediction / alpha estimate using model state from T-1.
4. Freeze the prediction.
5. Portfolio/backtest consumes prediction.
6. Only after the relevant outcome becomes available:
       compute the observation/label.
7. Update learner state.
8. Record update event.
```

Do NOT perform:

```text
observe future outcome
→ update model
→ generate historical prediction
```

That is leakage.

---

# 8. PREQUENTIAL EVALUATION

Implement **prequential / online evaluation**.

The fundamental sequence must be:

```text
predict
→ realize outcome
→ score prediction
→ update learner
→ next prediction
```

Never:

```text
fit on full sample
→ replay historical predictions
```

unless explicitly marked as a non-predictive diagnostic.

The evaluator must distinguish:

- predictive online evaluation;
- descriptive retrospective analysis;
- full-sample diagnostic.

Only the first may be used to support adaptive predictive claims.

---

# 9. BASELINE MODELS

Before implementing sophisticated online learning, implement strong baselines.

At minimum:

### Static baseline

Parameters fixed for the entire evaluation period.

### Expanding baseline

Training window expands through time.

### Rolling baseline

Fixed-length historical window.

### EWMA baseline

Exponentially weighted historical observations.

### No-adaptation baseline

Use the Prompt 06/07 alpha exactly as-is.

The adaptive system must demonstrate improvement against these baselines.

---

# 10. ROLLING LEARNING

Implement generic rolling estimation.

Parameters:

```text
window_size
minimum_observations
update_frequency
refit_frequency
```

Hard rules:

- window contains only information available before prediction;
- insufficient history returns an explicit unavailable state;
- no silent fallback to full-sample fitting;
- window identity is recorded;
- refit timestamps are recorded.

Support:

```text
rolling
expanding
anchored
```

where compatible with the existing validation framework.

---

# 11. EXPONENTIAL WEIGHTING

Implement exponentially weighted observations.

Support:

```text
half_life
decay_factor
minimum_effective_sample_size
```

Do not accept ambiguous decay semantics.

Document exactly how:

```text
weight(age)
```

is computed.

Expose effective sample size.

The system must warn when the selected half-life is so short that the learner effectively operates on too little information.

---

# 12. ALPHA DECAY ENGINE

Build a dedicated alpha decay analysis.

For each alpha:

Measure:

- IC over time;
- rank IC over time;
- quantile spread over time;
- hit rate;
- information ratio;
- decay curve;
- half-life;
- regime-conditioned decay;
- rolling performance;
- turnover-adjusted performance.

Do not assume exponential decay is correct.

Support multiple diagnostic forms where useful.

Return:

```text
DecayEstimate
```

with:

```text
method
estimate
confidence_interval
sample_size
fit_quality
stability
warnings
```

Do not manufacture a half-life when the data cannot support one.

Return `None` / `NOT_TESTED` / explicit insufficiency instead.

---

# 13. ALPHA EFFICACY STATE

Create a research-time representation of current alpha efficacy.

Conceptually:

```text
AlphaEfficacyState
```

may contain:

```text
alpha_id
timestamp
rolling_ic
rolling_rank_ic
rolling_hit_rate
rolling_spread
estimated_decay
sample_size
confidence
regime
drift_status
stability_status
```

This is descriptive/research information.

It is NOT permission to trade.

---

# 14. ADAPTIVE ENSEMBLE WEIGHTING

Implement versioned alpha ensemble adaptation.

Candidate methods may include:

```text
equal_weight
performance_weighted
IC_weighted
inverse_variance
exponential_performance_weighted
regime_conditioned
```

Every method must have:

- explicit mathematical definition;
- hyperparameters;
- PIT update semantics;
- minimum-history requirement;
- normalization policy;
- turnover implications;
- stability checks.

Do not allow a learner to select the method using future data.

---

# 15. SIGN CONTROL

Alpha direction must remain explicit.

Never infer direction from future performance inside a historical prediction.

Use existing:

```text
expected_direction
```

semantics.

If adaptive learning estimates direction, it must be treated as a separate research model and must obey a training/update boundary.

---

# 16. ONLINE BAYESIAN COMPONENT

Where practical, implement a minimal Bayesian online estimator.

Do not build an unnecessarily large Bayesian framework.

A useful first implementation could estimate:

```text
P(alpha_is_positive | observed_history)
```

or an equivalent posterior distribution over alpha efficacy.

Requirements:

- explicit prior;
- explicit likelihood;
- sequential update;
- prior identity/version;
- posterior state;
- credible interval;
- minimum observation requirement.

Never describe posterior probability as certainty.

Do not turn posterior probability directly into live orders.

---

# 17. CONTEXTUAL / REGIME-CONDITIONED ADAPTATION

Integrate Prompt 09.

Adaptive models may condition on:

```text
regime
state
volatility state
trend state
correlation state
dispersion state
```

But regime information must itself be PIT-valid.

Explicitly distinguish:

```text
filtered regime
```

from:

```text
smoothed retrospective regime
```

Predictive adaptive evaluation must not consume smoothed future-aware regime labels.

---

# 18. CONCEPT DRIFT

Implement drift diagnostics.

Potential methods:

```text
distributional drift
feature drift
alpha IC drift
residual drift
prediction-error drift
population stability
rolling statistical tests
CUSUM-compatible diagnostics
```

Reuse Prompt 09 change-detection concepts where appropriate.

Do not equate:

```text
drift detected
```

with:

```text
market regime changed
```

They are distinct concepts.

---

# 19. DRIFT STATE MACHINE

Provide explicit states, for example:

```text
STABLE
WATCH
DRIFT_DETECTED
INSUFFICIENT_DATA
UNAVAILABLE
```

State transitions must be deterministic and recorded.

Do not automatically reset a model merely because drift is detected.

Model reset/retraining must be an explicit research policy.

---

# 20. ADAPTATION POLICIES

Implement explicit policies such as:

```text
NO_ADAPTATION
ROLLING_REFIT
EXPANDING_REFIT
EWMA_UPDATE
DRIFT_TRIGGERED_REFIT
REGIME_CONDITIONAL
ENSEMBLE_ADAPTATION
```

Every policy must declare:

```text
update_frequency
training_window
minimum_history
trigger
parameters
fallback
```

Fallback must be explicit.

Never silently fall back to future information.

---

# 21. MODEL RESET POLICY

If drift or instability causes a reset:

Record:

```text
old_model_state_id
new_model_state_id
reset_time
reset_reason
trigger_metric
threshold
training_window
```

A reset is a research event.

It must appear in experiment lineage.

---

# 22. MODEL STABILITY

Build stability diagnostics for:

- parameter drift;
- sign changes;
- coefficient magnitude;
- alpha weights;
- feature importance;
- prediction distribution;
- forecast dispersion;
- ensemble concentration;
- turnover induced by adaptation.

Flag:

```text
weight concentration
parameter explosion
rapid oscillation
sign instability
insufficient history
unstable refits
```

Do not silently clip problematic parameters unless the clipping policy is explicitly part of the model definition.

---

# 23. ADAPTIVE ENSEMBLE CONSTRAINTS

The ensemble must support hard constraints such as:

```text
max_alpha_weight
min_alpha_weight
max_turnover
min_active_alphas
max_concentration
```

If constraints are infeasible:

```text
raise InfeasibleAdaptiveEnsemble
```

Do not silently relax them.

---

# 24. TEMPORAL CROSS-VALIDATION

Integrate with Prompt 05.

Adaptive models must support:

```text
walk-forward
rolling
expanding
anchored
purged
embargoed
```

where appropriate.

Training and validation periods must be explicitly represented.

No random IID train/test split for temporal prediction claims.

---

# 25. PREVENT ADAPTATION OVERFITTING

Adaptive systems are especially vulnerable to overfitting.

Test:

```text
different window sizes
different half-lives
different update frequencies
different drift thresholds
different ensemble weighting schemes
different regime conditioning
```

But do not simply select the best result and call it validated.

Record all tested configurations in the experiment ledger.

Apply Prompt 05 multiple-testing controls.

---

# 26. HYPERPARAMETER SELECTION

Implement strict separation:

```text
research / development
        ↓
training
        ↓
validation
        ↓
holdout
```

A final holdout must not be repeatedly inspected during adaptation design.

If a parameter is selected using the holdout, mark the experiment appropriately.

Do not claim independent OOS evidence after holdout contamination.

---

# 27. ONLINE LEARNING VS WALK-FORWARD

Make the distinction explicit.

### Online learning

Updates sequentially after observations arrive.

### Walk-forward refitting

Periodically retrains on a historical window.

### Expanding learning

Uses all historical observations available before each prediction.

### Static model

Never updates.

The framework must not label all four as "online learning."

---

# 28. PREQUENTIAL METRICS

Implement metrics appropriate for sequential predictions.

At minimum where applicable:

```text
IC
rank IC
MSE
MAE
directional accuracy
log loss
Brier score
calibration
hit rate
alpha spread
turnover
cost-adjusted return
drawdown
```

Metrics must state their observation frequency and sample size.

Do not report meaningless metrics when insufficient observations exist.

---

# 29. ADAPTIVE PERFORMANCE ATTRIBUTION

The system must answer:

> Did adaptation create the improvement, or did something else?

Compare:

```text
static alpha
vs
rolling alpha
vs
EWMA alpha
vs
adaptive ensemble
```

Attribute differences to:

```text
signal quality
timing
turnover
cost
risk
regime exposure
concentration
leverage
```

Use the existing backtester for final portfolio-level attribution.

---

# 30. COST-AWARE ADAPTATION

Adaptation can increase turnover.

Therefore every adaptive portfolio experiment must account for:

```text
commission
slippage
turnover
position changes
rebalance frequency
```

Use the existing Prompt 05 `CostSchedule`.

Do not introduce zero-cost adaptive backtests as the default.

A zero-cost result must be explicitly labeled as a diagnostic.

---

# 31. RISK INTEGRATION

Adaptive alpha weights must be compatible with Prompt 08.

Evaluate:

```text
beta
factor exposure
covariance
volatility
concentration
drawdown
stress
```

Do not allow adaptive alpha selection to bypass the risk layer.

---

# 32. PORTFOLIO INTEGRATION

The output chain must remain:

```text
Adaptive Alpha
      ↓
Alpha Ensemble
      ↓
Portfolio Constructor
      ↓
Risk Controls
      ↓
Existing Backtester
      ↓
Prompt 05 Validation
```

Never:

```text
Adaptive Alpha
      ↓
Broker
```

---

# 33. NULL / PLACEBO / ADVERSARIAL TESTS

Mandatory tests should include:

### Null alpha

No persistent predictive relationship.

### Permuted labels

Destroy temporal relationship.

### Time-shifted features

Detect leakage.

### Future-feature injection

Must FAIL.

### Future-label injection

Must FAIL.

### Random adaptive weights

Should not systematically produce strong alpha.

### Static-vs-adaptive synthetic control

Adaptive model must not automatically win.

### Regime-label leakage

Smoothed future-aware regimes must be rejected for predictive mode.

### Hyperparameter leakage

Future-selected parameters must FAIL integrity.

---

# 34. SYNTHETIC DATA

Use synthetic data only for architecture validation.

Create synthetic scenarios such as:

```text
stationary alpha
decaying alpha
regime-dependent alpha
sign-flipping alpha
drifting alpha
zero-alpha null
structural-break alpha
```

These scenarios should test whether the learner behaves as intended.

Do not present synthetic profitability as market evidence.

Synthetic experiments must remain capped by the existing research gate.

---

# 35. INTEGRITY FRAMEWORK

Extend existing integrity semantics.

Potential checks:

```text
PIT_AVAILABLE
NO_FUTURE_FEATURE
NO_FUTURE_LABEL
NO_FUTURE_REGIME
NO_FUTURE_PARAMETER_SELECTION
NO_HOLDOUT_CONTAMINATION
ONLINE_UPDATE_ORDER
TRAIN_TEST_SEPARATION
ADAPTATION_LINEAGE
COST_AWARE
MULTIPLE_TESTING_RECORDED
```

Use existing statuses:

```text
PASS
FAIL
WARN
NOT_TESTED
```

Never convert `NOT_TESTED` to `PASS` merely because an object exists.

---

# 36. RESEARCH GATE

Prompt 05 remains the only promotion gate.

Prompt 10 must NEVER create a new promotion mechanism.

Allowed outputs remain compatible with:

```text
REJECT
WARN
RESEARCH_CANDIDATE
PROMOTED_TO_PAPER
```

Synthetic data must remain incapable of promotion.

Integrity failure must prevent successful research promotion.

Adaptive improvement alone cannot promote an experiment.

---

# 37. EXPERIMENT LINEAGE

Every adaptive experiment must record:

```text
experiment_id
parent_experiment_id
data_snapshot
dataset_checksum
feature_ids
alpha_ids
regime_definition
learner_definition
window
half_life
update_frequency
hyperparameters
training_period
validation_period
holdout_period
random_seed
cost_schedule
risk_model
portfolio_definition
software_version
config_hash
integrity_report
research_gate_result
```

The ledger must make it possible to reproduce:

> exactly what information the learner had at each update.

---

# 38. CACHE SAFETY

Cache keys must include every research-defining input.

At minimum:

```text
dataset snapshot
feature identity
alpha identity
learner identity
window
decay
update frequency
regime identity
universe identity
date range
frequency
normalization
random seed
```

A future dataset append must not mutate a historical adaptive state.

---

# 39. REGISTRY

Create a versioned registry compatible with existing architecture.

Support:

```text
adaptive list
adaptive inspect
adaptive register
adaptive compare
```

Never overwrite an existing definition.

Formula or algorithm changes require a new version.

---

# 40. CLI

Extend the existing CLI without breaking commands.

Candidate interface:

```bash
quantlab adaptive list

quantlab adaptive inspect <id>

quantlab adaptive run <experiment>

quantlab adaptive state <experiment>

quantlab adaptive decay <alpha>

quantlab adaptive drift <experiment>

quantlab adaptive stability <experiment>

quantlab adaptive compare <a> <b>

quantlab adaptive prequential <experiment>

quantlab research adaptive <experiment>

quantlab research alpha-decay <alpha>

quantlab research adaptive-compare <a> <b>
```

Use the repository's existing CLI architecture rather than creating an unrelated parser.

---

# 41. DESKTOP INTEGRATION

The desktop must remain a thin Qt client.

Extend the application layer first:

```text
quantlab.app
```

Then expose read/query operations to:

```text
quantlab.ui
```

Possible UI:

```text
Adaptive Lab
├── Models
├── Online State
├── Alpha Decay
├── Drift
├── Ensemble Weights
├── Stability
├── Prequential Evaluation
├── Adaptive Comparison
└── Experiment Lineage
```

The UI must NOT:

- calculate models directly;
- read Parquet directly;
- bypass PIT;
- modify experiment records;
- bypass the research gate;
- place orders;
- enable live trading.

---

# 42. LIVE TRADING SAFETY

This is absolute.

Maintain:

```text
LIVE_TRADING=false
```

The adaptive engine must have no API capable of:

```text
REQUEST_LIVE_ORDER
```

and must not import:

```text
Zerodha
OpenAlgo
broker SDKs
```

into adaptive research code.

AI cannot use adaptive outputs to request live orders.

Do not add an emergency bypass.

---

# 43. OBSERVABILITY

Log:

```text
model update
prediction timestamp
outcome availability timestamp
update timestamp
training window
state transition
drift detection
reset
weight change
constraint event
insufficient-history event
integrity result
```

Avoid logging sensitive raw datasets unnecessarily.

---

# 44. ERROR HANDLING

Define explicit errors such as:

```text
AdaptiveError
FutureInformationError
InsufficientHistoryError
InvalidUpdateOrderError
AdaptiveModelError
DriftDetectionError
AdaptiveEnsembleError
InfeasibleAdaptiveEnsemble
HoldoutContaminationError
```

Do not silently catch and continue through integrity failures.

---

# 45. TESTING REQUIREMENTS

Add comprehensive tests.

At minimum cover:

### PIT

- future observation cannot affect current state;
- delayed outcome updates only after availability;
- appending future data does not alter historical state.

### Rolling

- exact window boundaries;
- insufficient-history behavior;
- no future rows.

### EWMA

- weight calculation;
- half-life;
- effective sample size.

### Online

- prediction-before-update;
- outcome-after-prediction;
- update ordering.

### Drift

- stable process;
- synthetic drift;
- false-positive control;
- explicit state transitions.

### Ensemble

- weights normalize correctly;
- constraints enforced;
- infeasibility raises;
- no future performance leakage.

### Regime

- predictive mode rejects smoothed future-aware labels.

### Validation

- walk-forward;
- purge;
- embargo;
- holdout contamination detection.

### Multiple testing

- all tested adaptive configurations are recorded.

### Safety

- no live order path;
- `LIVE_TRADING=false`;
- adaptive module cannot bypass risk firewall.

---

# 46. TYPE SAFETY AND CODE QUALITY

Maintain:

```text
ruff
mypy --strict
pytest
```

Use explicit types.

Avoid:

```text
Any
global mutable state
hidden singletons
implicit timezone assumptions
silent exception swallowing
```

Follow existing QUANT LAB conventions.

---

# 47. PERFORMANCE

Do not prematurely optimize.

First guarantee correctness.

Then optimize:

- rolling calculations;
- cached feature access;
- sequential updates;
- vectorized diagnostics;
- repeated experiment evaluation.

Do not sacrifice PIT correctness for speed.

If parallelizing experiments, ensure experiment state and random seeds remain deterministic.

---

# 48. DOCUMENTATION

Create/update appropriate documentation.

At minimum:

```text
docs/architecture/ADAPTIVE_ALPHA_ARCHITECTURE.md
docs/research/ONLINE_LEARNING.md
docs/research/ALPHA_DECAY.md
docs/research/CONCEPT_DRIFT.md
docs/research/ADAPTIVE_ENSEMBLES.md
docs/decisions/ADR-024-adaptive-alpha-online-learning.md
```

Adapt names to existing conventions if ADR numbering or document organization differs.

Document:

- mathematical definitions;
- temporal semantics;
- update order;
- limitations;
- failure modes;
- validation protocol;
- known `NOT_TESTED` areas.

---

# 49. ADR-024

Create an ADR documenting the architectural decision.

It should explicitly establish:

1. Adaptive engine is research-only.
2. Existing backtester remains canonical.
3. PIT semantics are mandatory.
4. Online prediction occurs before outcome update.
5. Static baselines are mandatory.
6. Adaptive improvement does not equal alpha.
7. Prompt 05 remains the sole promotion gate.
8. Synthetic results cannot promote.
9. Desktop remains a query client.
10. Live trading remains disabled.

---

# 50. REQUIRED RESEARCH COMPARISON

Implement a standard comparison experiment:

```text
STATIC
vs
ROLLING
vs
EXPANDING
vs
EWMA
vs
ADAPTIVE ENSEMBLE
```

For each report:

```text
prediction quality
IC
rank IC
alpha spread
turnover
cost
risk
drawdown
stability
drift
regime performance
OOS performance
statistical significance
multiple-testing adjustment
```

The report must explicitly answer:

```text
Did adaptation improve the signal?

Did adaptation improve after costs?

Did adaptation improve OOS?

Did adaptation increase turnover?

Did adaptation increase risk?

Did adaptation remain stable?

Was the comparison multiple-tested?

Does the evidence justify a stronger research status?
```

---

# 51. REQUIRED ALPHA HALF-LIFE STUDY

For selected alpha:

```text
alpha
→ rolling IC
→ decay curve
→ half-life estimate
→ confidence interval
→ regime-conditioned half-life
→ stability
```

Do not force a half-life if evidence is weak.

Return:

```text
ESTIMABLE
INSUFFICIENT_DATA
UNSTABLE
NOT_TESTED
```

as appropriate.

---

# 52. REQUIRED DRIFT EXPERIMENT

Create a synthetic test where:

```text
T0 → alpha works
T1 → alpha weakens
T2 → alpha disappears
T3 → alpha reverses
```

Verify:

- learner detects degradation;
- no future information is used;
- model state changes are recorded;
- adaptation occurs only according to the declared policy;
- reset does not use future labels;
- research ledger records all updates.

---

# 53. REQUIRED ADVERSARIAL TEST

Create an intentionally leaky adaptive learner.

Examples:

```text
uses future rolling IC
uses future normalization
uses future regime
selects half-life using final holdout
updates before prediction
```

The integrity framework MUST detect and reject these.

This test is mandatory.

---

# 54. DO NOT BUILD YET

Do NOT implement:

- reinforcement-learning trading agents;
- autonomous LLM traders;
- live Zerodha execution;
- OpenAlgo execution;
- broker-specific strategy logic;
- deep RL;
- high-frequency trading infrastructure;
- GPU training infrastructure;
- distributed cluster;
- cloud data pipeline;
- options execution;
- derivatives margin engine.

Those are future phases.

The objective is **research correctness first**.

---

# 55. ARCHITECTURAL QUALITY BAR

The final architecture should resemble a quantitative research platform rather than a collection of scripts.

Prefer:

```text
immutable definitions
typed domain models
deterministic pipelines
PIT data access
explicit temporal semantics
reproducible experiments
research lineage
strong validation
fail-closed safety
```

Avoid:

```text
magic heuristics
hidden state
global model objects
future-aware calculations
"best model" selection without accounting
untracked hyperparameter searches
UI-driven computation
broker coupling
```

---

# 56. ACCEPTANCE CRITERIA

Prompt 10 is complete only when all of the following are true.

### Architecture

- [ ] Existing 0.9 architecture preserved.
- [ ] Adaptive package integrated cleanly.
- [ ] No duplicate data fabric.
- [ ] No duplicate backtester.
- [ ] No duplicate research gate.

### Scientific correctness

- [ ] PIT update semantics implemented.
- [ ] Prequential evaluation implemented.
- [ ] Static baseline implemented.
- [ ] Rolling baseline implemented.
- [ ] Expanding baseline implemented.
- [ ] EWMA baseline implemented.
- [ ] Alpha decay analysis implemented.
- [ ] Drift diagnostics implemented.
- [ ] Adaptive ensemble implemented.
- [ ] Regime-conditioned adaptation implemented where valid.
- [ ] Stability diagnostics implemented.

### Integrity

- [ ] Future feature injection fails.
- [ ] Future label injection fails.
- [ ] Future regime injection fails.
- [ ] Future hyperparameter selection fails.
- [ ] Holdout contamination fails.
- [ ] Prediction/update ordering is tested.
- [ ] `NOT_TESTED` remains `NOT_TESTED`.

### Research

- [ ] Static vs adaptive comparison works.
- [ ] Cost-aware evaluation works.
- [ ] Multiple testing is recorded.
- [ ] Experiment lineage is complete.
- [ ] Synthetic scenarios validate expected behavior.

### Integration

- [ ] Prompt 05 validation still works.
- [ ] Prompt 07 portfolio construction still works.
- [ ] Prompt 08 risk engine still works.
- [ ] Prompt 09 regime engine still works.
- [ ] Desktop remains functional.
- [ ] CLI remains backward compatible.

### Safety

- [ ] `LIVE_TRADING=false`.
- [ ] No live-order capability.
- [ ] No broker imports in adaptive research code.
- [ ] AI cannot bypass safety gates.

### Quality

- [ ] Full pytest passes.
- [ ] ruff passes.
- [ ] `mypy --strict` passes.
- [ ] No known regression in Prompts 01–09.

---

# 57. FINAL VALIDATION COMMANDS

Before declaring completion, run the repository's canonical commands.

At minimum:

```bash
make test
ruff check .
mypy --strict src
```

Then execute relevant CLI smoke tests:

```bash
quantlab adaptive list
quantlab adaptive inspect <known-id>
quantlab adaptive decay <known-alpha>
quantlab adaptive drift <known-experiment>
quantlab adaptive prequential <known-experiment>
quantlab adaptive compare <static> <adaptive>
quantlab slice
```

Run the desktop smoke test if the repository supports it.

---

# 58. FINAL REPORT TO USER

When implementation is complete, report:

```text
QUANT LAB version
Prompt 10 status
tests passed
ruff status
mypy status
new modules
new CLI commands
new research capabilities
new ADR
new documentation
known NOT_TESTED items
known limitations
live-trading safety status
example commands
```

Also report:

```text
STATIC vs ADAPTIVE
```

results separately from any synthetic demonstration.

Never claim that synthetic adaptive performance constitutes real-market alpha.

---

# 59. FINAL ENGINEERING DIRECTIVE

Think like a quantitative researcher, statistical learning researcher, and safety-critical software architect simultaneously.

The purpose of Prompt 10 is NOT to make QUANT LAB "more AI."

The purpose is to make the research process capable of distinguishing:

```text
real adaptation
from
overfitting,

alpha decay
from
random variation,

concept drift
from
noise,

regime dependence
from
selection bias,

adaptive improvement
from
turnover-induced artifacts,

OOS robustness
from
in-sample optimization.
```

The strongest outcome may be:

```text
ADAPTATION DOES NOT HELP.
```

That is a valid and valuable scientific result.

Never optimize for impressive returns.

Optimize for:

```text
causal temporal correctness
+
statistical validity
+
reproducibility
+
robustness
+
auditability
+
fail-closed safety
```

Implement Prompt 10 completely on the existing QUANT LAB codebase.
Do not stop at scaffolding.
Do not create placeholder APIs that pretend to work.
Do not fabricate market data.
Do not fabricate performance.
Do not silently weaken validation to make tests pass.

**Build the smallest research-grade implementation that is scientifically defensible, fully integrated, testable, reproducible, and ready for the next QUANT LAB research layer.**
