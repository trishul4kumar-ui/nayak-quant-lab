# QUANT LAB — CURSOR MASTER PROMPT 09
# MARKET REGIME, STATE & TEMPORAL DYNAMICS ENGINE

**Version:** 0.9  
**Project:** QUANT LAB  
**Objective:** Extend QUANT LAB 0.8 into a research-grade Market Regime, State & Temporal Dynamics Engine while preserving every architectural, mathematical, PIT, validation, safety, and reproducibility invariant established by Prompts 01–08.

---

# 0. ABSOLUTE ENGINEERING DIRECTIVE

You are continuing the **existing QUANT LAB repository**.

**DO NOT RESET THE REPOSITORY.**  
**DO NOT rewrite Prompts 01–08.**  
**DO NOT create parallel data, feature, alpha, portfolio, risk, backtest, validation, ledger, or application engines.**

Before changing anything:

```text
INSPECT
→ MAP CURRENT ARCHITECTURE
→ TRACE EXISTING ABSTRACTIONS
→ IDENTIFY REUSE POINTS
→ WRITE/UPDATE ADR IF REQUIRED
→ IMPLEMENT IN SMALL VERTICAL SLICES
→ TEST
→ RUN FULL REGRESSION
→ DOCUMENT
```

Use the existing repository as the source of truth.

If an abstraction already exists, **extend it rather than duplicate it**.

---

# 1. CURRENT QUANT LAB BASELINE

Prompts 01–08 have established:

```text
01  Core quantitative research architecture
02  Research / execution safety architecture
03  Native desktop application
04  Point-in-Time Data Fabric
05  Research-Grade Backtesting & Validation Engine
06  Feature & Alpha Research Engine
07  Cross-Sectional Alpha & Portfolio Construction
08  Quantitative Risk & Factor Research
```

Current conceptual chain:

```text
PIT DATA
   ↓
FEATURES
   ↓
LABELS
   ↓
ALPHA
   ↓
FACTOR RESEARCH
   ↓
RISK MODEL
   ↓
PORTFOLIO CONSTRUCTION
   ↓
RISK FIREWALL
   ↓
BACKTEST
   ↓
VALIDATION
   ↓
RESEARCH GATE
   ↓
EXPERIMENT LEDGER
```

Prompt 09 introduces:

```text
MARKET STATE
   ↓
REGIME DETECTION
   ↓
TEMPORAL DYNAMICS
   ↓
REGIME-CONDITIONAL RESEARCH
```

Target architecture:

```text
                         PIT DATA FABRIC
                                │
                                ▼
                        MARKET OBSERVATIONS
                                │
                 ┌──────────────┼──────────────┐
                 ▼              ▼              ▼
              RETURNS       VOLATILITY     DISPERSION
                 │              │              │
                 └──────────────┼──────────────┘
                                ▼
                         MARKET STATE ENGINE
                                │
              ┌─────────────────┼──────────────────┐
              ▼                 ▼                  ▼
        STATE FEATURES    REGIME DETECTORS    TEMPORAL METRICS
              │                 │                  │
              └─────────────────┼──────────────────┘
                                ▼
                       REGIME CLASSIFICATION
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
        CURRENT STATE     TRANSITIONS       REGIME HISTORY
              │                 │                 │
              └─────────────────┼─────────────────┘
                                ▼
                    CONDITIONAL RESEARCH
                                │
          ┌─────────────────────┼────────────────────┐
          ▼                     ▼                    ▼
      ALPHA BY REGIME      RISK BY REGIME      FACTORS BY REGIME
          │                     │                    │
          └─────────────────────┼────────────────────┘
                                ▼
                       EXISTING BACKTEST
                                │
                                ▼
                       EXISTING VALIDATION
                                │
                                ▼
                         RESEARCH GATE
                                │
                                ▼
                       EXPERIMENT LEDGER
```

---

# 2. PRIMARY RESEARCH QUESTION

The engine must answer:

> **What was the observable market state at time T, how did that state evolve through time, which regimes can be identified without hindsight, and how do alpha, factor exposure, risk, and portfolio behavior change conditional on that state?**

The engine must distinguish:

```text
OBSERVATION
STATE
REGIME
REGIME TRANSITION
REGIME FORECAST
ALPHA
```

These are different scientific objects.

---

# 3. FUNDAMENTAL DOMAIN SEPARATION

Enforce:

```text
FEATURE ≠ MARKET STATE ≠ REGIME ≠ REGIME FORECAST ≠ ALPHA
```

Also:

```text
REGIME DETECTION ≠ REGIME FORECASTING
```

A classifier describing the current state is not a predictive model.

---

# 4. MARKET STATE DEFINITION

Create or extend a versioned:

```text
MarketState
```

Conceptually:

```text
MarketState
├── state_id
├── decision_time
├── universe_id
├── snapshot_id
├── feature_vector
├── state_variables
├── regime_id
├── regime_version
├── confidence
├── detection_method
├── lineage
└── integrity_status
```

Adapt naming to existing repository conventions.

Do not create duplicate state objects if one already exists.

---

# 5. MARKET STATE MUST BE POINT-IN-TIME

At time:

```text
T
```

the state may use only:

```text
available_time <= T
```

All inputs must originate from the existing PIT fabric.

Examples:

```text
returns
volatility
cross-sectional dispersion
correlation
volume
liquidity
breadth
factor returns
factor exposures
```

must be PIT-valid.

---

# 6. STATE SNAPSHOT IMMUTABILITY

Once:

```text
MarketState(T)
```

has been produced for a dataset snapshot, appending future observations must not modify it.

Mandatory regression test:

```text
append future data
→ recompute historical state
→ state(T) unchanged
```

---

# 7. MARKET STATE ≠ MARKET PREDICTION

The initial engine is descriptive/research-oriented.

It must not claim:

```text
"market will rise"
"market will fall"
"regime will continue"
```

merely because:

```text
regime = bull
```

A state label is not a forecast.

---

# 8. STATE FEATURE SOURCES

Reuse Prompt 06's feature infrastructure.

Potential state variables:

```text
market return
rolling return
realized volatility
downside volatility
cross-sectional dispersion
cross-sectional correlation
breadth
turnover
volume
liquidity proxies
factor returns
factor volatility
drawdown
trend strength
mean-reversion diagnostics
```

Only implement variables for which data actually exists.

---

# 9. NO DUPLICATE FEATURE ENGINE

Do not create:

```text
quantlab.regime.features
```

if the existing feature engine can provide the required measurements.

Preferred:

```text
quantlab.features
       ↓
MarketStateEngine
```

---

# 10. MARKET RETURN

Where a valid benchmark exists, calculate market return explicitly.

Do not invent:

```text
NIFTY
SENSEX
benchmark
index return
```

If no valid PIT benchmark exists:

```text
NOT_TESTED
```

---

# 11. CROSS-SECTIONAL DISPERSION

Where sufficient PIT data exists, support:

```text
Dispersion(T)
```

using an explicit mathematical definition.

Document whether it is:

```text
cross-sectional standard deviation
mean absolute deviation
median absolute deviation
```

or another method.

Do not silently switch definitions.

---

# 12. CROSS-SECTIONAL CORRELATION

Support a PIT-valid measure of average pairwise correlation or an equivalent documented statistic.

Requirements:

```text
minimum asset count
return window
frequency
missing-data policy
estimator
```

No sufficient sample:

```text
NOT_AVAILABLE
```

---

# 13. BREADTH

Where sufficient market data exists, prepare:

```text
advancers / decliners
fraction positive
fraction above moving average
cross-sectional sign balance
```

All definitions must be explicit.

---

# 14. VOLATILITY STATE

Reuse Prompt 06/08 infrastructure.

Potential state variables:

```text
realized volatility
EWMA volatility
volatility percentile
volatility acceleration
```

Never compute percentile using future observations.

---

# 15. CORRELATION STATE

Measure:

```text
average correlation
correlation percentile
correlation trend
```

using PIT-valid history.

---

# 16. DISPERSION STATE

Measure:

```text
current dispersion
rolling percentile
dispersion trend
```

without future normalization.

---

# 17. TREND STATE

Prepare transparent diagnostics:

```text
moving-average slope
price trend
cross-sectional momentum breadth
trend strength
```

These are state diagnostics, not alpha signals.

---

# 18. DRAWdown STATE

Where valid:

```text
market drawdown
cross-sectional drawdown
portfolio drawdown
```

must be computed from historical information only.

---

# 19. LIQUIDITY STATE

Where real data exists, prepare:

```text
volume regime
ADV regime
spread regime
turnover regime
```

If calibrated data is unavailable:

```text
NOT_TESTED
```

Do not fabricate liquidity.

---

# 20. STATE VECTOR

Create an explicit representation:

```text
S(T) =
[
  return,
  volatility,
  correlation,
  dispersion,
  breadth,
  liquidity,
  trend,
  drawdown,
  factor_state...
]
```

The actual vector must reflect available data.

Every component must have:

```text
feature_id
version
value
availability_time
quality
```

---

# 21. STATE NORMALIZATION

Support explicit historical normalization:

```text
z-score
rank percentile
robust z-score
rolling percentile
```

All reference distributions must be based only on:

```text
τ <= T
```

No future normalization.

---

# 22. ROLLING NORMALIZATION

For a rolling window:

```text
W(T) = {τ | T-L <= τ <= T}
```

where L is the explicit lookback.

Record:

```text
lookback
frequency
minimum observations
normalization method
```

---

# 23. EXPANDING NORMALIZATION

Support:

```text
W(T) = {τ | τ <= T}
```

where scientifically appropriate.

Avoid look-ahead through future normalization.

---

# 24. REGIME DEFINITION

A regime is:

> A persistent or recurring region of the observable market-state space characterized by a defined classification methodology.

Do not define regimes using future returns unless the research experiment explicitly labels them as future outcome labels rather than state definitions.

---

# 25. BASELINE REGIME ENGINE

Implement a transparent baseline first.

Possible approach:

```text
rule-based state buckets
```

Example:

```text
VOLATILITY
low / normal / high

TREND
negative / neutral / positive

CORRELATION
low / normal / high
```

Combine only where justified.

Do not create arbitrary regime counts merely to produce labels.

---

# 26. REGIME IDENTITY

Every regime model must be versioned:

```text
RegimeModel
├── regime_model_id
├── version
├── state_features
├── normalization
├── lookback
├── detector
├── parameters
├── universe
├── snapshot
└── configuration_hash
```

---

# 27. REGIME LABEL IMMUTABILITY

Do not overwrite historical labels.

A change to:

```text
threshold
lookback
feature
detector
number of states
```

creates a new model version.

---

# 28. HMM ARCHITECTURE

Prepare an extensible interface for:

```text
Hidden Markov Model
```

but do not make it mandatory if a transparent baseline is sufficient.

Important:

```text
HMM state inference must respect temporal availability.
```

---

# 29. HMM CAUTION

An HMM fitted over the entire historical sample can use future observations to infer earlier hidden states.

Therefore:

```text
FULL-SAMPLE HMM SMOOTHING
```

must not be used as a valid historical trading feature.

For historical research, support:

```text
filtered state
```

using observations available up to T.

If smoothing is used:

```text
mark as retrospective analysis
```

and prohibit its use in predictive/backtest context.

---

# 30. MARKOV TRANSITION MODEL

Prepare:

```text
P(R_{t+1}=j | R_t=i)
```

using historical transitions.

Record:

```text
sample period
regime version
transition counts
transition probabilities
```

---

# 31. TRANSITION MATRIX

Represent:

```text
             Next
           R1    R2    R3
Current R1
        R2
        R3
```

Rows must have explicit interpretation.

Handle:

```text
zero transition count
```

without fabricated probabilities.

---

# 32. TRANSITION ESTIMATION

Support explicit options:

```text
maximum likelihood
Laplace/Dirichlet smoothing
```

if justified.

Never silently smooth.

---

# 33. REGIME PERSISTENCE

Measure:

```text
duration
median duration
mean duration
distribution
```

using only observed regime history.

---

# 34. REGIME TRANSITIONS

Record:

```text
from_regime
to_regime
transition_time
transition_method
confidence
```

---

# 35. REGIME CONFIDENCE

If a probabilistic model exists, record:

```text
P(regime | information available at T)
```

Do not convert probability into certainty.

---

# 36. HARD LABEL VS PROBABILITY

Keep separate:

```text
hard_regime
```

and:

```text
regime_probabilities
```

Do not discard probabilistic information.

---

# 37. REGIME FORECASTING

Treat forecasting as a future extension.

If implemented later:

```text
REGIME DETECTOR
→ REGIME FORECAST MODEL
```

must be separate objects.

No current-state classifier should silently become a forecasting model.

---

# 38. REGIME CONDITIONED ALPHA

Reuse Prompt 06.

For alpha A:

```text
IC(A | Regime = r)
```

Report:

```text
IC
rank IC
hit rate
sample size
confidence interval
```

where statistically appropriate.

---

# 39. REGIME CONDITIONED PORTFOLIO

Reuse Prompt 07.

Compare:

```text
portfolio performance | regime
```

without changing the canonical backtester.

---

# 40. REGIME CONDITIONED RISK

Reuse Prompt 08.

Report:

```text
volatility | regime
beta | regime
factor exposure | regime
drawdown | regime
risk contribution | regime
```

---

# 41. REGIME CONDITIONED FACTORS

Reuse Prompt 08.

Analyze:

```text
factor return | regime
factor IC | regime
factor exposure | regime
factor correlation | regime
```

---

# 42. REGIME-CONDITIONAL PERFORMANCE

For any research experiment report:

```text
return
volatility
Sharpe
drawdown
turnover
IC
hit rate
```

by regime where sample size is sufficient.

---

# 43. SAMPLE SIZE WARNING

A regime with insufficient observations must produce:

```text
INSUFFICIENT_SAMPLE
```

or:

```text
NOT_AVAILABLE
```

not a misleading statistic.

---

# 44. REGIME COMPARISON

Compare regimes only when:

```text
definition is stable
data is comparable
sample size is adequate
```

---

# 45. MULTIPLE TESTING

Regime research creates substantial multiplicity:

```text
many regimes
many alphas
many factors
many lookbacks
many state variables
many thresholds
```

Record all tested hypotheses.

Prompt 05 remains the authoritative statistical validation and gate.

---

# 46. REGIME SELECTION BIAS

Never choose a regime because it produced the best historical result and then present that result as unbiased evidence.

The selection itself is a research choice.

Record:

```text
candidate regimes
selection method
selection date
experiment lineage
```

---

# 47. DATA SNOOPING

A regime should not be repeatedly tuned until an attractive backtest appears.

Prompt 05 must be used for formal validation.

---

# 48. REGIME STABILITY

Measure:

```text
label stability
feature stability
transition stability
duration stability
```

through time.

---

# 49. REGIME LABEL SWITCHING

For clustering-based methods, cluster IDs can permute.

Therefore distinguish:

```text
cluster identity
economic interpretation
```

Do not assume cluster 1 always means "bull."

---

# 50. CLUSTERING ARCHITECTURE

Prepare an extensible interface for:

```text
K-means
Gaussian mixture
hierarchical clustering
```

but implement only a transparent baseline initially.

---

# 51. CLUSTERING PIT SAFETY

A full-sample clustering fit may use future observations.

Therefore predictive use must use:

```text
expanding fit
rolling fit
walk-forward fit
```

with explicit training windows.

---

# 52. ONLINE / WALK-FORWARD REGIME FITTING

Prepare:

```text
train until T
infer state at T+1
```

where appropriate.

No future data in training.

---

# 53. REGIME MODEL TRAINING IDENTITY

Every fit should record:

```text
training_start
training_end
as_of
dataset_snapshot
model_version
configuration_hash
```

---

# 54. REGIME MODEL CACHE

Cache identity must include:

```text
snapshot
training window
as_of
state features
feature versions
normalization
detector
parameters
universe
```

---

# 55. TEMPORAL FEATURES

Prepare temporal diagnostics:

```text
lagged state
state change
state velocity
state acceleration
rolling mean
rolling variance
autocorrelation
```

These must be PIT-valid.

---

# 56. STATE VELOCITY

For state variable x:

```text
Δx_t = x_t - x_{t-1}
```

Keep units explicit.

---

# 57. STATE ACCELERATION

Where meaningful:

```text
Δ²x_t = Δx_t - Δx_{t-1}
```

Do not over-engineer.

---

# 58. AUTOCORRELATION

Provide explicit:

```text
lag
window
estimator
minimum observations
```

Do not silently assume stationarity.

---

# 59. STATIONARITY DIAGNOSTICS

Prepare interfaces for:

```text
ADF
KPSS
rolling statistics
distribution drift
```

Do not treat statistical stationarity tests as proof of stationarity.

---

# 60. CHANGE-POINT DETECTION

Prepare an extensible interface for:

```text
CUSUM
Page-Hinkley
Bayesian change-point architecture
```

Implement a simple baseline first.

---

# 61. CHANGE-POINT ≠ REGIME

A change-point indicates a structural/statistical shift.

It is not automatically a named regime.

Keep:

```text
ChangePoint
```

separate from:

```text
Regime
```

---

# 62. CHANGE-POINT OUTPUT

Record:

```text
timestamp
detector
threshold
signal
confidence if applicable
features
```

---

# 63. REGIME TRANSITION VS CHANGE-POINT

Maintain:

```text
transition = movement between classified states
change-point = detected statistical/distributional shift
```

These may coincide but are not identical.

---

# 64. TEMPORAL DEPENDENCE

Do not use IID assumptions for temporal market data unless explicitly justified.

Reuse Prompt 05's:

```text
moving-block bootstrap
sign-flip/null methods
```

where appropriate.

---

# 65. REGIME BOOTSTRAP

When estimating regime-conditioned statistics, preserve temporal dependence.

Do not randomly shuffle individual observations by default.

---

# 66. REGIME PERFORMANCE SIGNIFICANCE

A regime-conditioned Sharpe or IC should include:

```text
sample size
window
estimator
uncertainty method
```

where applicable.

---

# 67. REGIME COMPOSITION BIAS

Track whether a regime has:

```text
different universe size
different liquidity
different missingness
```

than other regimes.

---

# 68. UNIVERSE CONSISTENCY

Use:

```text
Universe(T)
```

from the PIT fabric.

Do not let regime research use today's universe.

---

# 69. CORPORATE ACTIONS

Reuse Prompt 04 policy.

Do not create a separate corporate-action interpretation.

---

# 70. MARKET CALENDAR

Reuse the existing calendar service.

Do not create another calendar implementation.

---

# 71. TIME FREQUENCY

Support explicit:

```text
daily
intraday
```

only where data supports it.

Do not assume daily and intraday states are interchangeable.

---

# 72. TIMEZONE

Indian-market research must explicitly represent:

```text
Asia/Kolkata
```

where applicable.

Do not mix:

```text
UTC
local exchange time
system time
```

implicitly.

---

# 73. SESSION BOUNDARIES

Use the existing calendar conventions.

Do not create synthetic official holidays.

---

# 74. INTRADAY STATE

If intraday data is later introduced:

```text
state(T)
```

must respect the exact information boundary within the session.

No use of the day's closing price before the close.

---

# 75. END-OF-DAY STATE

Clearly distinguish:

```text
close-derived state
```

from:

```text
intraday state
```

---

# 76. REGIME CONDITIONING IN BACKTESTS

The backtester must consume regime information exactly as it would have been known at decision time.

Correct:

```text
state(T)
→ strategy decision at T
→ next-bar fill
```

Incorrect:

```text
full-history regime(T)
→ strategy decision at T
```

if full-history fitting used future data.

---

# 77. NO SECOND BACKTESTER

Do not create a regime-specific backtester.

Reuse:

```text
run_backtest
```

and existing execution assumptions.

---

# 78. NO SECOND VALIDATION ENGINE

Prompt 05 remains authoritative.

---

# 79. NO SECOND DATA FABRIC

Prompt 04 remains authoritative.

---

# 80. NO SECOND FEATURE ENGINE

Prompt 06 remains authoritative.

---

# 81. NO SECOND PORTFOLIO OPTIMIZER

Prompt 07 remains authoritative.

---

# 82. NO SECOND RISK ENGINE

Prompt 08 remains authoritative.

---

# 83. REGIME-AWARE STRATEGY INTERFACE

Prepare an optional interface:

```text
Strategy
    ↓
MarketState
    ↓
Regime information
```

But do not automatically change strategy behavior based on regime.

---

# 84. REGIME-AWARE ALPHA

Prepare:

```text
AlphaCondition
```

or equivalent.

It should be able to express:

```text
evaluate alpha under regime R
```

without mutating the alpha definition.

---

# 85. REGIME-AWARE PORTFOLIO

Prepare:

```text
PortfolioCondition
```

only as a research abstraction.

No direct order generation.

---

# 86. REGIME-AWARE RISK

Allow analysis of:

```text
risk limits by regime
```

but do not allow a regime classifier to bypass the existing firewall.

---

# 87. RISK FIREWALL

The existing firewall remains authoritative.

Even if:

```text
regime = low risk
```

the system cannot bypass:

```text
RiskLimits
RiskState
HALT
EMERGENCY
```

---

# 88. AI BOUNDARY

AI may:

```text
summarize regimes
propose hypotheses
explain transitions
compare experiments
```

AI may NOT:

```text
override regime model
override PIT
override risk
override integrity
override research gate
request live orders
enable live trading
```

---

# 89. REGIME RESEARCH REPORT

Create or extend a report:

```text
QUANT LAB MARKET REGIME REPORT
==============================

Regime Model:
Version:
Detector:

DATA
----
Dataset:
Snapshot:
Universe:
Frequency:
Timezone:

STATE VARIABLES
---------------
Feature:
Version:
Coverage:
Missing:
Normalization:

REGIMES
-------
ID:
Definition:
Observations:
Share:
Mean Duration:
Median Duration:

TRANSITIONS
-----------
Transition Matrix:
Persistence:
Change Points:

STATE QUALITY
-------------
PIT:
Leakage:
Stability:
Sample Adequacy:

CONDITIONAL ALPHA
-----------------
Alpha:
Regime:
IC:
Rank IC:
Hit Rate:
Decay:

CONDITIONAL RISK
----------------
Volatility:
Beta:
Factor Exposure:
Drawdown:
Risk Contribution:

LIMITATIONS
-----------

VALIDATION
----------
OOS:
Walk-forward:
Robustness:
Statistics:

RESEARCH GATE
-------------
Status:
Reasons:
```

---

# 90. MACHINE-READABLE REGIME RESULT

A regime result should be serializable with:

```text
regime_model_id
regime_version
decision_time
state_id
hard_regime
regime_probabilities
confidence
dataset_id
snapshot_id
universe_id
integrity_status
```

---

# 91. EXPERIMENT LEDGER

Every regime experiment must enter the existing ledger.

Record:

```text
regime_model
state features
feature versions
dataset
snapshot
universe
training window
detector
parameters
configuration hash
validation result
```

---

# 92. REPRODUCIBILITY

Same:

```text
snapshot
training window
feature versions
detector
parameters
seed
code version
```

must produce the same result within documented numerical tolerance.

---

# 93. RANDOMNESS

If clustering/HMM/model fitting uses randomness:

```text
seed must be explicit
```

Record it in experiment metadata.

---

# 94. RANDOM SEED ≠ STATISTICAL VALIDITY

A fixed seed provides reproducibility.

It does not make a model statistically valid.

---

# 95. REGIME MODEL SELECTION

If multiple models are compared:

```text
rule-based
K-means
GMM
HMM
```

treat model selection as an experiment.

Do not pick the most profitable model and call that unbiased validation.

---

# 96. MODEL COMPARISON

Compare:

```text
interpretability
stability
predictive utility
sample adequacy
computational cost
OOS behavior
```

not only backtest return.

---

# 97. REGIME ECONOMIC INTERPRETATION

A regime label should have:

```text
mathematical definition
state characteristics
statistical evidence
```

Economic labels such as:

```text
bull
bear
crisis
risk-on
risk-off
```

must be documented interpretations, not hidden assumptions.

---

# 98. REGIME LABEL CALIBRATION

If a regime is named:

```text
HIGH_VOL
```

show why:

```text
volatility distribution
threshold/model
sample period
```

supports that name.

---

# 99. REGIME COUNT

Do not optimize regime count for attractive strategy results.

Prefer:

```text
parsimony
stability
interpretability
```

---

# 100. REGIME OVERFITTING

Guard against:

```text
too many regimes
too many thresholds
too many state variables
too many model variants
```

---

# 101. REGIME CONDITIONAL ALPHA DECAY

Reuse Prompt 06 decay engine.

Analyze:

```text
alpha decay | regime
```

without creating another decay engine.

---

# 102. REGIME CONDITIONAL FACTOR CORRELATION

Reuse Prompt 08 factor engine.

Analyze:

```text
factor correlation | regime
```

where sample size supports it.

---

# 103. REGIME CONDITIONAL COVARIANCE

Reuse Prompt 08 covariance engine.

Potential research:

```text
Σ_regime
```

must be estimated only from observations assigned to that regime using valid historical classification.

---

# 104. COVARIANCE SAMPLE SIZE

A regime-specific covariance matrix can become unstable.

Require:

```text
minimum observations
```

and explicit status.

---

# 105. REGIME COVARIANCE SHRINKAGE

Reuse Prompt 08 estimators.

Do not create a new shrinkage implementation.

---

# 106. REGIME RISK STRESS

Reuse Prompt 08 stress framework.

Allow scenarios such as:

```text
high-volatility regime
high-correlation regime
large factor shock
liquidity deterioration
```

Scenarios remain hypothetical.

---

# 107. REGIME TRANSITION STRESS

Prepare analysis:

```text
current regime
→ historically observed transition
→ portfolio impact
```

where valid.

Do not forecast the transition.

---

# 108. REGIME-BASED RISK LIMITS

Prepare research-only analysis of:

```text
risk budget by regime
```

but maintain:

```text
RiskFirewall
```

as the sole safety authority.

---

# 109. REGIME FEATURE IMPORTANCE

If model-based classification is used, provide diagnostics such as:

```text
feature contribution
feature sensitivity
```

only where mathematically meaningful.

Do not fabricate explainability.

---

# 110. MODEL CONFIDENCE

Confidence must have a defined statistical meaning.

Do not use arbitrary scores such as:

```text
confidence = 0.87
```

without defining what 0.87 means.

---

# 111. UNCERTAINTY

Where probabilistic inference is unavailable:

```text
confidence = NOT_AVAILABLE
```

not a fabricated number.

---

# 112. REGIME QUALITY SCORE

If a quality score is introduced, document its formula.

Never create opaque:

```text
regime_quality = magic_number
```

---

# 113. STATE QUALITY

Each state should expose:

```text
data completeness
input validity
sample adequacy
normalization validity
PIT status
```

---

# 114. REGIME INTEGRITY

Regime results must integrate with the existing Research Integrity system.

Potential checks:

```text
future state feature
future normalization
future benchmark
future universe
future fitting
full-sample smoothing
```

must be detected.

---

# 115. FULL-SAMPLE FIT DETECTION

Explicitly distinguish:

```text
retrospective_fit
```

from:

```text
historical_predictive_fit
```

Retrospective models may be useful for exploratory analysis but must not enter a predictive backtest without proper walk-forward fitting.

---

# 116. SMOOTHING DETECTION

For HMM/state-space models:

```text
filtered estimate
```

may be eligible for predictive research.

```text
smoothed estimate
```

uses future information and must be blocked from predictive use.

---

# 117. FUTURE LABEL DETECTION

Do not allow:

```text
future return
future drawdown
future volatility
```

to define a regime used as a contemporaneous trading feature.

If used for outcome analysis, label it explicitly.

---

# 118. REGIME AS LABEL

It is valid to define a future regime transition as a research label.

Example:

```text
transition within H days
```

But it must remain:

```text
LABEL
```

not:

```text
FEATURE
```

---

# 119. TEMPORAL CLASSIFICATION

Where regime classification is predictive, enforce:

```text
train(T)
→ infer(T+1)
```

not:

```text
fit(all data)
→ infer historical state
```

---

# 120. WALK-FORWARD REGIME VALIDATION

Integrate with Prompt 05's walk-forward framework.

Do not build a second walk-forward engine.

---

# 121. PURGE / EMBARGO

If regime labels overlap future horizons, reuse Prompt 05's:

```text
purge
embargo
```

logic.

---

# 122. REGIME-CONDITIONAL STATISTICS

All statistics must state:

```text
regime definition
sample period
sample size
frequency
```

---

# 123. TEMPORAL CROSS-VALIDATION

Do not use random K-fold cross-validation for temporal regime models unless the experiment explicitly justifies it and prevents leakage.

Prefer:

```text
rolling
expanding
walk-forward
```

---

# 124. REGIME MODEL PERFORMANCE

If a regime model predicts future states, evaluate:

```text
accuracy
balanced accuracy
log loss
Brier score
transition prediction
calibration
```

only where appropriate.

A descriptive regime detector does not need predictive classification metrics.

---

# 125. REGIME CALIBRATION

For probabilistic models, test:

```text
calibration
reliability
probability quality
```

Do not equate high-confidence output with correctness.

---

# 126. REGIME DRIFT

Detect when:

```text
state distribution
```

changes materially.

Possible diagnostics:

```text
rolling mean drift
variance drift
distribution distance
population stability
```

Use explicit methods.

---

# 127. CONCEPT DRIFT

Prepare an architecture distinction:

```text
covariate drift
concept drift
regime transition
```

Do not treat them as synonyms.

---

# 128. DISTRIBUTION DISTANCE

Prepare interfaces for:

```text
KS
Wasserstein
PSI
```

where statistically appropriate.

Do not use one metric indiscriminately.

---

# 129. STATE SPACE

The system should be capable of representing a market as:

```text
S_t ∈ ℝ^n
```

and investigating temporal movement through that state space.

---

# 130. STATE DISTANCE

Where useful, support:

```text
Euclidean
Mahalanobis
robust distance
```

with explicit covariance handling.

---

# 131. MAHALANOBIS SAFETY

If covariance is singular or ill-conditioned:

```text
FAIL / UNEVALUABLE
```

or use an explicit documented regularization.

Never silently invert an unstable matrix.

---

# 132. REGIME SIMILARITY

Support research such as:

```text
current state
→ nearest historical states
```

but clearly label this as similarity analysis, not prediction.

---

# 133. ANALOG SEARCH

Prepare:

```text
historical analogs
```

using PIT state vectors.

Any resulting future outcomes are labels for retrospective research.

Do not leak them into contemporaneous state features.

---

# 134. TEMPORAL NEAREST NEIGHBORS

Avoid overlapping/self-matching issues.

Document:

```text
distance metric
exclusion window
minimum history
```

---

# 135. STATE CLUSTER VALIDATION

For clustering diagnostics, where applicable:

```text
silhouette
intra-cluster dispersion
inter-cluster separation
stability
```

Do not use clustering scores as proof of economic regimes.

---

# 136. REGIME ECONOMIC VALIDATION

Ask:

```text
Are regimes statistically distinguishable?
Are they temporally stable?
Do they produce interpretable state distributions?
Do they survive OOS?
```

not simply:

```text
Did one regime make money?
```

---

# 137. NULL REGIME TEST

Create null/permutation diagnostics where appropriate.

Examples:

```text
permuted state labels
block-preserving null
random regime assignment
```

Do not use IID permutation blindly for temporal data.

---

# 138. REGIME ALPHA NULL TEST

Test whether apparent:

```text
alpha | regime
```

could arise from random regime assignment or multiple testing.

Prompt 05 remains the formal gate.

---

# 139. REGIME SELECTION LEDGER

Record all candidate regime definitions.

Example:

```text
volatility threshold:
20%
25%
30%

lookback:
20
60
120

regime count:
2
3
4
```

The system must make search breadth visible.

---

# 140. RESEARCH GATE

Prompt 05 remains authoritative.

Regime research cannot directly produce:

```text
RESEARCH_CANDIDATE
```

unless it satisfies the existing gate.

Synthetic results remain constrained by existing policy.

---

# 141. SYNTHETIC DATA

Synthetic regimes may be used to test:

```text
detection
transitions
PIT
state calculations
```

but:

```text
synthetic regime discovery != market evidence
```

---

# 142. SYNTHETIC TEST DESIGN

Create synthetic datasets with:

```text
known low-vol regime
known high-vol regime
known transition
known persistence
```

to validate algorithmic behavior.

---

# 143. FALSE POSITIVE TEST

Create a null synthetic dataset where no meaningful regime structure exists.

Expected:

```text
no fabricated strong regime conclusion
```

---

# 144. FUTURE DATA TEST

Append future observations.

Expected:

```text
historical MarketState unchanged
historical regime inference unchanged
historical transition history unchanged
```

for models configured in PIT-safe mode.

---

# 145. FUTURE FIT TEST

Deliberately fit a model using future data.

Expected:

```text
integrity FAIL
```

or established leakage status.

---

# 146. FULL-SAMPLE HMM TEST

Verify:

```text
smoothed state
```

is marked retrospective and blocked from predictive/backtest use.

---

# 147. WALK-FORWARD HMM TEST

Verify filtered/walk-forward state inference does not use future observations.

---

# 148. FUTURE NORMALIZATION TEST

Deliberately normalize using future observations.

Expected:

```text
FAIL
```

---

# 149. FUTURE UNIVERSE TEST

Historical regime features must not change when future membership is appended.

---

# 150. SAMPLE ADEQUACY TEST

Tiny regimes must produce:

```text
INSUFFICIENT_SAMPLE
```

not fake confidence.

---

# 151. NUMERICAL TESTS

Test:

```text
NaN
Inf
constant state variable
zero variance
singular covariance
near-singular covariance
empty state vector
single observation
duplicate timestamps
duplicate security IDs
```

---

# 152. TEMPORAL ORDER TEST

Input observations deliberately shuffled.

The engine must:

```text
sort deterministically
```

or:

```text
reject invalid ordering
```

according to existing repository conventions.

---

# 153. DUPLICATE TIME TEST

Duplicate observations must not be silently aggregated.

Require explicit policy:

```text
reject
deduplicate using documented rule
```

---

# 154. TIMEZONE TEST

Verify:

```text
Asia/Kolkata
```

conversion does not change temporal ordering or availability semantics.

---

# 155. TRANSITION MATRIX TEST

Rows should satisfy:

```text
Σ_j P(i→j) = 1
```

within tolerance when valid probabilities exist.

Zero-count rows must have explicit handling.

---

# 156. REGIME DURATION TEST

Validate duration calculations against known synthetic sequences.

---

# 157. STATE NORMALIZATION TEST

Verify future observations cannot change historical normalized values.

---

# 158. REPRODUCIBILITY TEST

Same inputs and seed produce identical outputs.

---

# 159. DESKTOP INTEGRATION

Extend the existing desktop application through:

```text
quantlab.app
```

Potential pages:

```text
Market State
Regime Lab
Transitions
Temporal Dynamics
Regime Alpha
Regime Risk
Regime Diagnostics
```

---

# 160. UI BOUNDARY

Desktop UI must NOT:

```text
read Parquet directly
fit HMM independently
run clustering independently
calculate state independently
modify regime models
modify ledger
bypass integrity
bypass research gate
bypass risk firewall
```

UI calls application services.

---

# 161. CLI

Extend the existing CLI rather than creating another framework.

Potential commands:

```text
quantlab state list
quantlab state inspect <id>
quantlab state compute <id>

quantlab regime list
quantlab regime inspect <id>
quantlab regime fit <id>
quantlab regime classify <id>
quantlab regime transitions <id>
quantlab regime durations <id>

quantlab research regime <experiment>
quantlab research regime-alpha <alpha> <regime>
quantlab research regime-risk <portfolio> <regime>
quantlab research regime-correlation
```

Use actual existing CLI naming conventions where different.

---

# 162. API / APPLICATION SERVICES

Prefer:

```text
quantlab.app
```

for orchestration.

Domain modules should remain independent of Qt.

---

# 163. PACKAGE STRUCTURE

Inspect existing structure first.

A possible target is:

```text
quantlab/
├── state/
│   ├── models.py
│   ├── engine.py
│   ├── normalization.py
│   ├── diagnostics.py
│   └── repository.py
│
├── regimes/
│   ├── models.py
│   ├── definitions.py
│   ├── detectors.py
│   ├── transitions.py
│   ├── duration.py
│   ├── clustering.py
│   ├── hmm.py
│   ├── change_points.py
│   ├── validation.py
│   └── repository.py
│
└── temporal/
    ├── dynamics.py
    ├── stationarity.py
    ├── drift.py
    └── diagnostics.py
```

**Do not blindly create this structure.**

Adapt it to the existing QUANT LAB architecture.

---

# 164. DOMAIN OBJECTS

Potential objects:

```text
MarketState
StateDefinition
StateObservation
RegimeDefinition
RegimeModel
RegimeObservation
RegimeTransition
TransitionMatrix
ChangePoint
TemporalDiagnostic
RegimeResearchResult
```

Reuse existing models where possible.

---

# 165. REPOSITORY / PERSISTENCE

Use the established persistence conventions.

Do not introduce a second database architecture.

---

# 166. CACHE

Use existing cache infrastructure.

No separate cache database unless architecturally justified.

---

# 167. CONFIGURATION

All parameters must be explicit and hashable:

```text
lookback
frequency
features
normalization
detector
thresholds
number of regimes
seed
training window
```

---

# 168. CONFIG HASH

A change to any material parameter must change:

```text
configuration_hash
```

and therefore experiment identity.

---

# 169. LINEAGE

Every regime result must answer:

```text
Which dataset?
Which snapshot?
Which universe?
Which features?
Which feature versions?
Which detector?
Which training period?
Which parameters?
Which code version?
```

---

# 170. OBSERVABILITY

Expose:

```text
STATE
REGIME
CONFIDENCE
PIT STATUS
MODEL VERSION
TRAINING WINDOW
SAMPLE SIZE
DATA QUALITY
```

---

# 171. ERROR HANDLING

Explicitly fail for:

```text
missing state inputs
future data
invalid timestamps
insufficient observations
invalid covariance
invalid regime parameters
NaN/Inf
```

No silent fallback.

---

# 172. FORBIDDEN FALLBACKS

Never do:

```text
missing volatility → 0
missing correlation → 0
missing regime → bull
missing probability → 1
missing benchmark → invented benchmark
future state → use latest available future row
insufficient observations → fabricate statistic
```

---

# 173. UNKNOWN SEMANTICS

Preserve:

```text
NOT_TESTED
NOT_AVAILABLE
INSUFFICIENT_SAMPLE
UNEVALUABLE
FAIL
WARN
PASS
```

with their established semantics.

---

# 174. REGIME QUALITY STATUS

A regime model can be:

```text
EXPLORATORY
RESEARCH_VALIDATED
RESEARCH_CANDIDATE
```

only through existing research governance.

Do not invent a second promotion system.

---

# 175. RESEARCH QUESTIONS TO ENABLE

The engine should make experiments such as these possible:

```text
H1:
Momentum alpha behaves differently across volatility regimes.

H2:
Momentum alpha weakens during high-correlation regimes.

H3:
Low-volatility portfolios have different factor exposures
during stress regimes.

H4:
Portfolio drawdowns cluster around specific state transitions.

H5:
Risk estimates become less stable during high-correlation regimes.

H6:
Factor diversification changes materially across regimes.

H7:
A regime-conditioned portfolio improves OOS robustness
relative to an unconditional baseline.

H8:
Regime conditioning adds no statistically significant value.
```

The last outcome is equally valuable.

---

# 176. REGIME-CONDITIONED RESEARCH PROTOCOL

For every hypothesis:

```text
1. Define regime before outcome inspection.
2. Define state variables.
3. Define PIT boundary.
4. Define training window.
5. Define regime detector.
6. Define alpha/portfolio.
7. Define evaluation period.
8. Run baseline.
9. Run conditional analysis.
10. Apply Prompt 05 validation.
11. Record all alternatives tested.
12. Record result in ledger.
```

---

# 177. BASELINE COMPARISON

Every regime-conditioned strategy experiment should compare against:

```text
unconditional strategy
```

using the same:

```text
dataset
snapshot
universe
costs
backtester
validation protocol
```

---

# 178. INCREMENTAL VALUE TEST

Ask:

```text
Does regime information add information beyond:
alpha
factor exposures
risk model
```

Do not assume it does.

---

# 179. REGIME INTERACTION

Prepare architecture for:

```text
alpha × regime
factor × regime
risk × regime
portfolio × regime
```

but avoid uncontrolled interaction explosion.

---

# 180. MULTIPLE-TESTING BOUNDARY

If many regime interactions are tested:

```text
Prompt 05
```

must receive the complete experiment family metadata.

---

# 181. REGIME-BASED FEATURE SELECTION

Do not automatically select features based on the best regime-conditioned result.

Treat selection as a research experiment.

---

# 182. TEMPORAL CAUSALITY

Do not claim:

```text
regime caused return
```

merely because:

```text
return differed by regime
```

The system reports association unless a causal design exists.

---

# 183. REGIME LABEL SEMANTICS

Use neutral identifiers:

```text
REGIME_0
REGIME_1
REGIME_2
```

internally.

Human labels may be attached as metadata.

---

# 184. REGIME DESCRIPTION

Provide summaries:

```text
mean volatility
mean correlation
mean dispersion
mean breadth
mean market return
factor environment
```

These summaries must be descriptive.

---

# 185. REGIME HEATMAP DATA

Prepare data for desktop visualization:

```text
time × state variable
time × regime
regime × alpha
regime × factor
regime × risk
```

The UI remains presentation-only.

---

# 186. TRANSITION GRAPH

Prepare machine-readable transition graph:

```text
nodes = regimes
edges = transitions
weight = probability/count
```

This is a research visualization, not a forecast.

---

# 187. REGIME TIMELINE

Expose:

```text
date
regime
probability
state variables
transition flag
```

---

# 188. STATE TRAJECTORY

Support:

```text
state_t
→
state_{t+1}
```

analysis.

No future state may be used for current-state decisions.

---

# 189. TEMPORAL CLUSTERING

If temporal clustering is introduced, preserve chronology.

Do not destroy time structure through random shuffling.

---

# 190. REGIME MODEL BENCHMARKS

At minimum establish:

```text
rule-based baseline
```

before sophisticated models.

Later compare:

```text
rule-based
clustering
HMM
```

using the same research protocol.

---

# 191. COMPLEXITY CONTROL

Do not implement every regime algorithm in Prompt 09.

Priority:

```text
P0:
MarketState
PIT normalization
rule-based regime
transition matrix
duration
conditional alpha/risk
integrity tests

P1:
walk-forward clustering
change-point baseline
temporal diagnostics

P2:
HMM
probabilistic regimes
advanced drift detection
```

Only advance when the previous layer is stable.

---

# 192. PERFORMANCE

Prioritize correctness.

Use:

```text
NumPy
Pandas/Polars if already established
DuckDB
existing cache
```

according to current project conventions.

Do not introduce distributed infrastructure.

---

# 193. MEMORY / DATA EFFICIENCY

Avoid materializing unnecessary full-history matrices.

Use:

```text
windowed computation
cached state features
incremental processing
```

where appropriate.

---

# 194. DETERMINISTIC SORTING

All outputs must have deterministic ordering.

Use:

```text
security_id
timestamp
regime_id
```

as appropriate.

---

# 195. LOGGING

Log:

```text
model ID
version
as_of
training window
detector
state features
sample count
status
```

---

# 196. SECURITY IDENTITY

Never use ticker strings as primary identity.

Use:

```text
security_id
```

with ticker as a label.

---

# 197. DATASET IDENTITY

Always preserve:

```text
dataset_id
snapshot_id
checksum
```

where applicable.

---

# 198. RESEARCH ARTIFACT IMMUTABILITY

Do not mutate prior:

```text
state results
regime results
transition matrices
experiment records
```

Create new versions.

---

# 199. REGRESSION REQUIREMENT

After implementation:

```text
make test
ruff
mypy --strict
```

and existing project commands.

Do not report completion until the complete existing suite passes.

---

# 200. BACKWARD COMPATIBILITY

Verify:

```text
quantlab slice
quantlab backtest
quantlab validate
quantlab research
quantlab feature
quantlab alpha
quantlab portfolio
quantlab factor
quantlab risk
quantlab desktop
```

remain functional.

Use actual commands discovered in the repository.

---

# 201. ACCEPTANCE CRITERIA

Prompt 09 is complete only when:

```text
✓ Prompts 01–08 remain intact.
✓ PIT fabric remains authoritative.
✓ Feature engine remains authoritative.
✓ Alpha engine remains authoritative.
✓ Portfolio constructor remains authoritative.
✓ Risk engine remains authoritative.
✓ Backtester remains authoritative.
✓ Validation engine remains authoritative.
✓ Research gate remains authoritative.
✓ Experiment ledger remains authoritative.

✓ MarketState abstraction exists.
✓ MarketState is versioned/traceable.
✓ State computation is PIT-safe.
✓ Future observations cannot alter historical state.
✓ State normalization is PIT-safe.
✓ State quality diagnostics exist.

✓ Baseline regime detector exists.
✓ Regime model is versioned.
✓ Regime labels are immutable.
✓ Regime transition model exists.
✓ Transition matrix is validated.
✓ Regime duration statistics exist.
✓ Hard labels and probabilities remain separate.

✓ Rule-based regime baseline exists.
✓ Architecture exists for clustering.
✓ Architecture exists for HMM.
✓ HMM smoothing is explicitly blocked from predictive use.
✓ Walk-forward fitting architecture exists.
✓ Change-point abstraction exists.
✓ Change-point ≠ regime.

✓ Regime-conditioned alpha research exists.
✓ Regime-conditioned factor research exists.
✓ Regime-conditioned risk research exists.
✓ Regime-conditioned portfolio research exists.
✓ Existing engines are reused.

✓ Temporal diagnostics exist.
✓ Stationarity architecture exists.
✓ Drift architecture exists.
✓ State velocity/acceleration architecture exists.

✓ Future normalization test exists.
✓ Future state test exists.
✓ Future model-fit test exists.
✓ Future universe test exists.
✓ HMM smoothing leakage test exists.
✓ Temporal-order tests exist.
✓ numerical edge-case tests exist.
✓ insufficient-sample tests exist.
✓ reproducibility tests exist.

✓ Experiment lineage exists.
✓ Configuration hash exists.
✓ Seed is recorded.
✓ Search breadth is recorded.
✓ Multiple-testing metadata is preserved.

✓ Desktop integrates through quantlab.app.
✓ UI does not compute regimes independently.
✓ UI does not bypass PIT.
✓ UI does not bypass validation.
✓ UI does not bypass risk firewall.

✓ No broker connectivity.
✓ No Zerodha/Kite execution.
✓ No OpenAlgo execution.
✓ No autonomous trading.
✓ LIVE_TRADING=false.
✓ AI cannot override safety boundaries.

✓ Existing tests pass.
✓ New tests pass.
✓ ruff clean.
✓ mypy --strict clean.
```

---

# 202. CRITICAL INVARIANTS

## INVARIANT 1 — PIT

```text
State(T) depends only on information available at T.
```

## INVARIANT 2 — NO FUTURE NORMALIZATION

Historical state normalization cannot depend on future observations.

## INVARIANT 3 — NO FULL-SAMPLE PREDICTIVE FIT

A model fitted using future observations cannot be used to create a historical predictive feature.

## INVARIANT 4 — FILTERED ≠ SMOOTHED

Filtered state:

```text
uses information through T
```

Smoothed state:

```text
may use information after T
```

Smoothed states are retrospective unless explicitly validated otherwise.

## INVARIANT 5 — REGIME ≠ FORECAST

Current classification is not a prediction.

## INVARIANT 6 — REGIME ≠ ALPHA

A regime label is not a trading signal.

## INVARIANT 7 — REGIME ≠ CAUSALITY

Conditional performance is association unless a causal design exists.

## INVARIANT 8 — MISSING ≠ ZERO

Unknown state variables remain unknown.

## INVARIANT 9 — ONE ENGINE

No duplicate:

```text
feature
backtest
risk
portfolio
validation
PIT
ledger
```

engines.

## INVARIANT 10 — HISTORICAL UNIVERSE

Use:

```text
Universe(T)
```

not today's survivors.

## INVARIANT 11 — SYNTHETIC

```text
synthetic regime detection ≠ evidence of tradable market regimes
```

## INVARIANT 12 — RESEARCH GATE

Prompt 05 remains the sole formal promotion gate.

## INVARIANT 13 — RISK FIREWALL

Regime information cannot override risk controls.

## INVARIANT 14 — AI

AI cannot override:

```text
PIT
Integrity
Risk
Constraints
Research Gate
Live Safety
```

## INVARIANT 15 — LIVE

```text
LIVE_TRADING=false
```

---

# 203. FORBIDDEN IMPLEMENTATIONS

Do NOT introduce:

```text
live trading
broker execution
Zerodha/Kite integration
OpenAlgo execution
autonomous trading
LLM regime decisions
LLM risk decisions
future-looking regime labels
full-sample HMM smoothing for backtests
full-sample clustering for predictive historical states
future normalization
today's universe for historical regimes
invented NIFTY data
invented liquidity data
invented fundamentals
```

---

# 204. FINAL RESEARCH LAB TARGET

After Prompt 09, QUANT LAB should be capable of investigating:

```text
WHAT MARKET STATE EXISTED AT T?
          ↓
HOW WAS THAT STATE DEFINED?
          ↓
WHAT REGIME DID THE PIT-SAFE MODEL ASSIGN?
          ↓
HOW CONFIDENT WAS THAT CLASSIFICATION?
          ↓
HOW LONG DID THAT REGIME PERSIST?
          ↓
HOW DID IT TRANSITION?
          ↓
HOW DID ALPHA BEHAVE IN THAT REGIME?
          ↓
HOW DID FACTOR EXPOSURES CHANGE?
          ↓
HOW DID PORTFOLIO RISK CHANGE?
          ↓
DID THE RELATIONSHIP SURVIVE OOS?
          ↓
DID IT SURVIVE COSTS?
          ↓
DID IT SURVIVE MULTIPLE-TESTING CONTROL?
          ↓
IS THE RESULT ROBUST?
          ↓
WHAT DOES THE RESEARCH GATE SAY?
```

---

# 205. SCIENTIFIC STANDARD

QUANT LAB must not be engineered to prove:

```text
"regime-aware trading is better."
```

It must be engineered to determine whether:

```text
regime information contains
incremental,
PIT-valid,
statistically defensible,
economically interpretable,
out-of-sample
information.
```

Possible successful outcomes include:

```text
REGIME EFFECT EXISTS
```

or:

```text
REGIME EFFECT DISAPPEARS AFTER CONTROL
```

or:

```text
REGIME EFFECT IS UNSTABLE
```

or:

```text
REGIME DETECTION HAS NO INCREMENTAL VALUE
```

All are legitimate research results.

---

# 206. FINAL ENGINEERING DIRECTIVE

Build Prompt 09 as a **scientific Market Regime, State & Temporal Dynamics laboratory**.

The architecture must evolve to:

```text
PIT DATA
   ↓
STATE VARIABLES
   ↓
MARKET STATE
   ↓
REGIME DETECTION
   ↓
TEMPORAL DYNAMICS
   ↓
REGIME-CONDITIONAL
 ┌──────────────┬──────────────┬──────────────┐
 ▼              ▼              ▼
ALPHA          FACTOR          RISK
 │              │              │
 └──────────────┼──────────────┘
                ▼
           PORTFOLIO
                ↓
           BACKTEST
                ↓
       WALK-FORWARD / OOS
                ↓
      STATISTICAL VALIDATION
                ↓
          RESEARCH GATE
                ↓
        EXPERIMENT LEDGER
```

Every material operation must remain:

```text
PIT-valid
versioned
deterministic
traceable
reproducible
mathematically explicit
temporally correct
statistically honest
falsifiable
```

**Do not reset QUANT LAB 0.8.0.**

**Do not duplicate existing engines.**

**Do not let full-sample hindsight leak into historical regime states.**

**Do not confuse regime detection with forecasting.**

**Do not confuse regime with alpha.**

**Do not bypass Prompt 05.**

**Do not bypass the RiskFirewall.**

**Do not introduce live execution.**

**Extend the laboratory.**
