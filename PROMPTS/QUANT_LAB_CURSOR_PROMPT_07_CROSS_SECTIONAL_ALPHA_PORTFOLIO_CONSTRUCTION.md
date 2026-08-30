# QUANT LAB — CURSOR MASTER PROMPT 07
# CROSS-SECTIONAL ALPHA RESEARCH & PORTFOLIO CONSTRUCTION

**Version:** 0.7  
**Date:** 2026-08-30  
**Project:** QUANT LAB  
**Mission:** Extend QUANT LAB 0.6 into a research-grade cross-sectional alpha and portfolio-construction laboratory without breaking the existing PIT data fabric, backtester, validation engine, research gate, or live-trading safety boundary.

---

# 0. EXECUTIVE DIRECTIVE

You are continuing the **existing QUANT LAB repository**.

This is NOT a greenfield implementation.

## NON-NEGOTIABLE

**DO NOT RESET THE REPOSITORY.**

**DO NOT rewrite Prompts 01–06.**

**DO NOT create a second:**

- PIT data fabric
- backtesting engine
- validation engine
- experiment ledger
- research integrity engine
- risk firewall
- application service layer

Prompt 07 must extend the existing system.

Preserve all established invariants:

```text
PIT available_time <= decision_time
historical universe(T)
next-bar execution
10 bps default transaction costs
risk firewall
Research Integrity Engine
experiment lineage
experiment ledger
reproducibility
NOT_TESTED != PASS
synthetic evidence != market evidence
LIVE_TRADING=false
AI cannot request live orders
desktop is a client of quantlab.app
```

Before modifying code:

```text
INSPECT
→ MAP
→ RECONCILE
→ DESIGN
→ IMPLEMENT
→ TEST
→ VALIDATE
→ DOCUMENT
```

Never assume that an abstraction does not already exist. Search the repository first.

---

# 1. PURPOSE

QUANT LAB currently has:

```text
01  Core architecture
02  Quantitative engine + safety
03  Desktop application
04  Point-in-Time Data Fabric
05  Research-Grade Backtesting & Validation
06  Feature & Alpha Research Engine
```

Prompt 07 introduces:

> **CROSS-SECTIONAL ALPHA RESEARCH & PORTFOLIO CONSTRUCTION**

The research question changes from:

```text
Does feature X contain predictive information?
```

to:

```text
How can multiple cross-sectional predictive signals be transformed into
a diversified, constrained, risk-aware portfolio without destroying
the statistical and economic properties of the underlying alpha?
```

The architecture must distinguish:

```text
FEATURE
    ↓
ALPHA
    ↓
ALPHA ENSEMBLE
    ↓
PORTFOLIO TARGET
    ↓
PORTFOLIO CONSTRUCTION
    ↓
RISK CONTROL
    ↓
EXECUTABLE ORDERS
```

These are separate domains.

---

# 2. CORE PRINCIPLE

Portfolio construction is NOT alpha discovery.

Do not allow an optimizer to hide arbitrary alpha selection.

The correct research chain is:

```text
Hypothesis
   ↓
Feature
   ↓
Alpha
   ↓
Alpha Validation
   ↓
Alpha Ensemble
   ↓
Portfolio Construction
   ↓
Risk Analysis
   ↓
Backtest
   ↓
OOS Validation
```

A portfolio optimizer must not be allowed to manufacture predictive power that does not exist in the underlying alpha research.

---

# 3. RESEARCH PHILOSOPHY

Do not optimize for:

```text
maximum backtest return
maximum in-sample Sharpe
minimum historical drawdown
single best parameter
single best optimizer result
```

Optimize for:

```text
robustness
diversification
risk-adjusted alpha
economic interpretability
stable exposures
controlled turnover
cost awareness
capacity awareness
out-of-sample persistence
reproducibility
```

A rejected portfolio is a valid research result.

A portfolio with high return but unstable leverage/exposure is not automatically good.

A portfolio with low raw return but robust risk-adjusted behavior may be scientifically valuable.

---

# 4. ARCHITECTURAL POSITION

Build on the existing architecture:

```text
                         QUANT LAB
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
   DATA FABRIC         RESEARCH ENGINE       APPLICATION
        │                   │                   │
        ▼                   ▼                   ▼
    PIT Store          Features / Labels       PySide6
        │                   │
        ▼                   ▼
   MarketState             Alpha
                              │
                              ▼
                       Alpha Ensemble
                              │
                              ▼
                    Portfolio Construction
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
                  Risk     Constraints  Costs
                    │         │         │
                    └─────────┼─────────┘
                              ▼
                         Target Weights
                              │
                              ▼
                         Risk Firewall
                              │
                              ▼
                         Backtester
                              │
                              ▼
                       Prompt 05 Validation
                              │
                              ▼
                       Research Gate
                              │
                              ▼
                       Experiment Ledger
```

There must remain a single canonical path through the existing research stack.

---

# 5. FIRST TASK — REPOSITORY RECONNAISSANCE

Before implementation inspect:

```text
src/quantlab/
features/
labels/
alpha/
research/
portfolio/
risk/
backtest/
validation/
data/
ledger/
integrity/
app/
ui/
CLI
existing genome AST
existing strategy abstractions
existing MarketState
existing portfolio abstractions
```

Search for existing implementations of:

```text
Portfolio
Position
Weight
TargetWeight
Exposure
Risk
Constraint
Optimizer
Covariance
Alpha
Signal
Genome
Strategy
```

Reuse and extend them where appropriate.

Do not create parallel abstractions.

---

# 6. DEFINITIONS

Formalize these concepts.

## Feature

A measurable transformation of information available at T.

```text
Feature(T)
```

## Alpha

A transformation of one or more features intended to express predictive information.

```text
Alpha(T)
```

## Alpha Ensemble

A deterministic combination of multiple validated or research-stage alpha signals.

```text
A(T) = f(A1(T), A2(T), ..., An(T))
```

## Portfolio Target

Desired portfolio weights:

```text
w_target(T)
```

## Executed Portfolio

Portfolio actually held after:

```text
fills
costs
constraints
risk controls
```

These must not be conflated.

---

# 7. CROSS-SECTIONAL ALPHA MODEL

At each decision time T:

```text
Universe(T)
      ↓
Feature values
      ↓
Alpha values
      ↓
Cross-sectional normalization
      ↓
Alpha score
      ↓
Portfolio construction
```

The universe must be PIT-correct.

---

# 8. PIT REQUIREMENT

At decision time T:

```text
ONLY information available at or before T
```

may affect:

```text
alpha values
ranking
normalization
covariance
risk estimates
portfolio constraints
portfolio weights
```

This includes:

```text
market data
universe membership
sector classification
market cap
beta
volatility
correlation
factor exposure
liquidity
```

If an input is not PIT-valid:

```text
NOT_TESTED
```

or fail the integrity gate where appropriate.

---

# 9. CROSS-SECTIONAL UNIVERSE

At every rebalance:

```text
U(T)
```

must be resolved from the existing PIT universe service.

Do not use:

```text
today's surviving securities
```

for historical research.

Record:

```text
universe_id
universe_version
as_of
security_count
eligible_count
```

---

# 10. ALPHA SCORE MATRIX

Create a conceptual structure:

```text
                 Security
             A       B       C       D
Alpha 1     0.8     0.2    -0.4     0.7
Alpha 2     0.1     0.6     0.3    -0.2
Alpha 3    -0.4     0.2     0.8     0.1
```

The engine must preserve:

```text
security_id
decision_time
alpha_id
alpha_version
value
```

Do not rely on ticker strings as primary identity.

---

# 11. ALPHA NORMALIZATION

Support explicit transformations:

```text
raw score
rank
percentile
cross-sectional z-score
robust z-score
winsorized z-score
```

Each transformation must be versioned/configured.

---

# 12. ALPHA SIGN CONVENTION

Every alpha must define:

```text
expected_direction
```

For example:

```text
+1 = higher score → higher expected return
-1 = higher score → lower expected return
```

The sign must not be silently flipped because a backtest looks better.

If sign is changed, create a distinct alpha transformation/experiment.

---

# 13. ALPHA STANDARDIZATION

Do not assume that two alphas are comparable merely because both are called:

```text
score
```

Standardization must be explicit.

Examples:

```text
zscore(alpha_1)
rank(alpha_2)
```

must remain distinguishable.

---

# 14. ALPHA CORRELATION

Build a cross-sectional alpha correlation framework.

Measure, where statistically appropriate:

```text
Pearson correlation
Spearman correlation
```

Across:

```text
time
securities
cross-sectional scores
```

The methodology must be explicit.

Do not collapse all correlation concepts into one number.

---

# 15. ALPHA RETURN CORRELATION

Also distinguish:

```text
score correlation
```

from:

```text
realized return correlation
```

Two alphas can have:

```text
high score correlation
```

but different:

```text
portfolio behavior
```

or vice versa.

---

# 16. ALPHA IC MATRIX

Build infrastructure for:

```text
Alpha × Horizon
```

and:

```text
Alpha × Alpha
```

research.

Record:

```text
IC
Rank IC
IC volatility
IC hit rate
IC decay
```

Prompt 05 remains responsible for formal validation/gating.

---

# 17. ALPHA ENSEMBLE

Create a first-class ensemble object.

Conceptually:

```text
AlphaEnsemble
├── ensemble_id
├── version
├── components
├── weights
├── normalization
├── expected_direction
├── combination_method
├── constraints
└── lineage
```

Example:

```text
Ensemble E1

40% momentum_20
30% momentum_60
20% reversal_5
10% volatility_signal
```

Every component and weight must be recorded.

---

# 18. ENSEMBLE METHODS

Initial supported methods:

```text
equal weight
fixed explicit weights
rank average
z-score average
weighted rank
```

Do not implement opaque machine-learning weighting yet.

---

# 19. WEIGHT OPTIMIZATION

Prepare architecture for future optimized alpha weights.

But do NOT allow unrestricted optimization against the final test set.

Any learned weights must be:

```text
trained
validated
frozen
tested OOS
```

and integrated with Prompt 05's walk-forward framework.

---

# 20. ALPHA DIVERSIFICATION

The research system must investigate whether adding an alpha actually adds information.

Measure:

```text
marginal IC
incremental IC
correlation
incremental return
incremental risk
```

A new alpha should not be considered valuable simply because it has positive standalone performance.

---

# 21. ALPHA CONTRIBUTION

For an ensemble:

```text
Total Alpha
```

should be decomposable into component contributions where mathematically meaningful.

Record:

```text
component weight
component exposure
component contribution
```

---

# 22. PORTFOLIO TARGET

Create a clear target-weight abstraction.

Example:

```text
TargetPortfolio
├── decision_time
├── security_id
├── target_weight
├── source_ensemble
├── risk_profile
├── constraints
└── lineage
```

Target weights are NOT orders.

---

# 23. LONG-ONLY PORTFOLIO

Support a baseline long-only constructor.

Constraints:

```text
w_i >= 0
Σ w_i <= 1
```

Optional:

```text
cash >= 0
```

No leverage unless explicitly configured.

---

# 24. LONG-SHORT PORTFOLIO

Prepare a separate long-short constructor.

Constraints may include:

```text
Σ long weights
Σ short absolute weights
gross exposure
net exposure
```

Example:

```text
gross = Σ |w_i|
net   = Σ w_i
```

Do not assume:

```text
gross = 1
```

without explicit configuration.

---

# 25. RANK-BASED PORTFOLIO

Implement a transparent baseline:

```text
rank alpha
      ↓
top N
      ↓
equal weight
```

and:

```text
bottom N
      ↓
equal weight
```

for long-short research where permitted.

This provides a clean baseline against which optimizers can be compared.

---

# 26. SCORE-WEIGHTED PORTFOLIO

Support:

```text
w_i ∝ positive(score_i)
```

or an explicitly defined long-short transformation.

Document exact mathematics.

Avoid arbitrary clipping without recording it.

---

# 27. VOLATILITY TARGETING

Prepare a portfolio-level volatility targeting mechanism.

Conceptually:

```text
raw portfolio
      ↓
estimated volatility
      ↓
scaling factor
      ↓
target volatility
```

The volatility estimate must be PIT-valid.

Do not use future realized volatility to size historical positions.

---

# 28. POSITION CAPS

Support:

```text
max_position_weight
min_position_weight
```

Constraints must be explicit.

---

# 29. CONCENTRATION

Measure:

```text
max weight
top-5 weight
top-10 weight
Herfindahl-Hirschman Index
effective number of positions
```

Do not rely only on number of holdings.

---

# 30. TURNOVER

Define turnover explicitly.

For portfolio weights:

```text
Turnover(T)
=
0.5 × Σ |w_target_i(T) - w_pretrade_i(T)|
```

or another documented convention.

Do not change the convention between reports.

---

# 31. TURNOVER CONSTRAINT

Prepare:

```text
max_turnover
```

as a portfolio construction constraint.

The constraint must interact with transaction-cost assumptions.

---

# 32. TRANSACTION COST AWARENESS

Portfolio construction must expose:

```text
estimated transaction cost
```

but must NOT create a second cost model.

Use the existing Prompt 05 cost framework.

---

# 33. SLIPPAGE

Do not invent a new slippage model.

Use the existing slippage abstraction.

If configured impact is unavailable:

```text
NOT_TESTED / UNEVALUABLE
```

as appropriate.

---

# 34. LIQUIDITY

Prepare:

```text
ADV
participation rate
liquidity constraints
```

but do not fabricate real liquidity data.

If unavailable:

```text
NOT_TESTED
```

---

# 35. CAPACITY

Prepare architecture for:

```text
portfolio capital
ADV
participation
estimated impact
capacity
```

Capacity is a future research capability if current data is insufficient.

---

# 36. BETA EXPOSURE

Where PIT beta data is available, support:

```text
beta constraint
beta neutrality
beta reporting
```

Example:

```text
portfolio beta ≈ 0
```

for market-neutral research.

If beta is not available:

```text
NOT_TESTED
```

---

# 37. SECTOR EXPOSURE

Where PIT sector classification exists:

```text
sector_weight
sector_overweight
sector_underweight
```

Support constraints such as:

```text
|sector_weight - benchmark_weight| <= limit
```

Do not use today's sector labels historically.

---

# 38. MARKET-CAP EXPOSURE

Where PIT market-cap information exists:

```text
large
mid
small
```

or continuous size exposure.

Do not implement a fake market-cap source.

---

# 39. FACTOR EXPOSURE

Prepare architecture for:

```text
momentum
value
size
quality
volatility
market beta
```

factor exposures.

Do not claim factor neutrality unless the factor definitions and PIT data exist.

---

# 40. BENCHMARK

A portfolio may be evaluated against:

```text
benchmark
```

but QUANT LAB must not invent NIFTY data.

If no real benchmark exists:

```text
benchmark = NOT_AVAILABLE
```

not a fabricated series.

---

# 41. COVARIANCE MATRIX

Prepare a covariance estimation service.

Initial methods:

```text
sample covariance
```

and architecture for:

```text
exponentially weighted covariance
shrinkage covariance
robust covariance
```

Do not add every estimator immediately.

---

# 42. COVARIANCE PIT

Covariance at T must use only:

```text
data available by T
```

The lookback window and estimator must be recorded.

Example:

```text
covariance_window = 60 sessions
estimator = sample
as_of = T
```

---

# 43. COVARIANCE STABILITY

Measure:

```text
condition number
eigenvalues
rank
positive semidefinite validity
```

A numerically unstable covariance matrix must not silently enter optimization.

---

# 44. PSD ENFORCEMENT

If a covariance estimator can produce a non-PSD matrix:

```text
detect
record
repair only through an explicit documented method
```

Do not silently alter the matrix.

---

# 45. MINIMUM VARIANCE

Prepare a transparent optimizer:

```text
minimize:
    wᵀΣw
```

subject to explicit constraints.

Do not allow future information.

---

# 46. MEAN-VARIANCE

Prepare architecture for:

```text
maximize:
    expected_returnᵀw
    - λ wᵀΣw
```

But:

```text
expected_return
```

must come from a documented alpha model.

Do not derive expected returns from future realized returns.

---

# 47. RISK PARITY

Prepare a risk-budgeting interface.

Target:

```text
risk contribution_i ≈ target_i
```

Do not implement a black-box optimizer without diagnostics.

---

# 48. EQUAL RISK CONTRIBUTION

If implemented:

```text
RC_i = w_i × (Σw)_i / portfolio_volatility
```

must be defined and tested.

---

# 49. RISK CONTRIBUTION

Every portfolio report should be capable of decomposing:

```text
portfolio risk
```

into:

```text
security contribution
alpha contribution where meaningful
factor contribution where available
sector contribution where available
```

---

# 50. MARGINAL RISK

Prepare:

```text
marginal contribution to risk
```

and:

```text
component contribution to risk
```

for optimizer diagnostics.

---

# 51. CONSTRAINT ENGINE

Create a reusable portfolio constraint layer.

Conceptually:

```text
Constraint
├── id
├── type
├── scope
├── lower_bound
├── upper_bound
├── active
└── provenance
```

Potential constraints:

```text
weight
gross exposure
net exposure
turnover
sector
beta
factor
concentration
cash
```

---

# 52. CONSTRAINT PRIORITY

Do not allow optimization failure to silently relax safety constraints.

Distinguish:

```text
HARD CONSTRAINT
```

from:

```text
SOFT CONSTRAINT
```

Hard constraints must remain binding.

---

# 53. INFEASIBLE PORTFOLIOS

If constraints cannot be simultaneously satisfied:

```text
FAIL / INFEASIBLE
```

Do not silently:

```text
drop constraints
```

or:

```text
relax limits
```

---

# 54. RISK FIREWALL

Portfolio construction remains downstream of:

```text
Research
```

and upstream of:

```text
Execution
```

The existing risk firewall remains authoritative.

If:

```text
HALT
```

or:

```text
EMERGENCY
```

then no new exposure may be generated.

---

# 55. TARGET WEIGHT ≠ ORDER

This distinction is mandatory.

```text
TargetWeight
```

is a research/portfolio object.

```text
Order
```

is an execution object.

Prompt 07 must not introduce broker execution.

---

# 56. REBALANCING

Support configurable rebalance schedules:

```text
daily
weekly
monthly
event-driven
```

Only implement what current architecture requires.

The rebalance timestamp must be explicit.

---

# 57. HOLDING PERIOD

A portfolio must define:

```text
rebalance frequency
```

and not confuse it with:

```text
alpha prediction horizon
```

These are different.

---

# 58. ALPHA HORIZON VS REBALANCE HORIZON

Example:

```text
alpha predicts 20-day return
portfolio rebalances every 5 days
```

This is valid but must be explicit.

Do not automatically equate:

```text
prediction horizon = holding period
```

---

# 59. PORTFOLIO DRIFT

Track:

```text
pre-trade weights
target weights
post-trade weights
```

The difference must be attributable to:

```text
price movement
trading
costs
constraints
```

where the engine supports it.

---

# 60. PORTFOLIO ATTRIBUTION

Build a research-grade attribution structure.

At minimum prepare:

```text
return attribution
risk attribution
alpha contribution
sector contribution
factor contribution
```

where the required data exists.

---

# 61. ALPHA ATTRIBUTION

For an ensemble:

```text
Alpha A
Alpha B
Alpha C
```

track:

```text
standalone signal
ensemble weight
marginal effect
```

Avoid claiming exact attribution where the mathematics does not support it.

---

# 62. PORTFOLIO COMPARISON

Support comparisons such as:

```text
Alpha-only portfolio
vs
Equal-weight ensemble
vs
Risk-controlled ensemble
vs
Minimum-variance portfolio
```

All must use the SAME:

```text
dataset
PIT rules
backtester
cost schedule
validation protocol
```

unless explicitly changed.

---

# 63. BASELINE PORTFOLIOS

Implement transparent baselines where useful:

```text
equal weight
top-N equal weight
rank weight
market-neutral top/bottom
```

These provide research controls.

---

# 64. BENCHMARK PORTFOLIO

Where a valid benchmark exists, allow:

```text
benchmark comparison
```

Otherwise:

```text
NOT_AVAILABLE
```

Do not fabricate benchmark returns.

---

# 65. ALPHA ENSEMBLE RESEARCH

For each ensemble evaluate:

```text
standalone alpha IC
ensemble IC
ensemble correlation
portfolio return
risk
turnover
cost
drawdown
OOS performance
```

Prompt 05 remains the formal validation layer.

---

# 66. DIVERSIFICATION VALUE

A new alpha should be evaluated on:

```text
incremental information
```

and:

```text
incremental portfolio value
```

not merely:

```text
positive standalone return
```

---

# 67. ALPHA CORRELATION REGIMES

Correlation may change through time.

Analyze:

```text
rolling alpha correlation
```

where data permits.

Identify:

```text
stable correlation
correlation breakdown
correlation convergence
```

---

# 68. REGIME-AWARE PORTFOLIOS

Prepare architecture for evaluating portfolio behavior by regime:

```text
bull
bear
high volatility
low volatility
high dispersion
low dispersion
```

Use Prompt 05's regime infrastructure where available.

Do not create a second regime engine.

---

# 69. PORTFOLIO ROBUSTNESS

Every portfolio configuration should be capable of testing:

```text
different rebalance frequency
different top-N
different costs
different slippage
different weight caps
different volatility targets
different alpha weights
```

Parameter sweeps must remain traceable.

---

# 70. OPTIMIZER OVERFITTING

Optimization itself creates multiple-testing risk.

Record:

```text
optimizer
objective
constraints
parameter grid
number of configurations
selection method
training period
validation period
test period
```

Never hide optimizer search history.

---

# 71. WALK-FORWARD PORTFOLIO OPTIMIZATION

Prepare integration with Prompt 05:

```text
TRAIN
   ↓
fit alpha weights / covariance / optimizer parameters
   ↓
VALIDATE
   ↓
freeze configuration
   ↓
TEST
```

No future test information may influence the optimization.

---

# 72. PORTFOLIO MODEL IDENTITY

A portfolio model must have immutable identity.

Conceptually:

```text
PortfolioModel
├── portfolio_id
├── version
├── alpha_ensemble
├── optimizer
├── constraints
├── covariance_model
├── risk_target
├── rebalance_frequency
├── cost_assumptions
└── configuration_hash
```

---

# 73. PORTFOLIO CONFIGURATION HASH

The identity/hash must change when meaningful configuration changes.

Include as appropriate:

```text
alpha versions
weights
optimizer
constraints
risk target
covariance estimator
lookback
rebalance schedule
```

---

# 74. LINEAGE

A target portfolio must trace back to:

```text
dataset snapshot
universe
features
labels where relevant
alphas
ensemble
optimizer
constraints
risk model
configuration
code version
```

---

# 75. PORTFOLIO ARTIFACTS

Produce machine-readable artifacts.

Conceptually:

```text
portfolio_experiment/
    config.json
    alpha_inputs.json
    ensemble.json
    covariance.json
    constraints.json
    target_weights.parquet/json
    exposures.json
    turnover.json
    risk.json
    attribution.json
    validation.json
    integrity.json
    lineage.json
```

Follow existing artifact conventions.

---

# 76. EXPERIMENT LEDGER

Use the existing ledger.

Do not create another ledger.

Record:

```text
experiment_id
portfolio_id
portfolio_version
ensemble_id
dataset_id
snapshot_id
universe_id
configuration_hash
optimizer
constraints
risk_model
rebalance_frequency
validation_result
integrity_result
gate_result
```

---

# 77. RESEARCH FAMILY

Group related portfolio experiments.

Examples:

```text
FAMILY: MOMENTUM_ENSEMBLES
FAMILY: MARKET_NEUTRAL
FAMILY: RISK_PARITY
FAMILY: LOW_TURNOVER
```

This helps Prompt 05 understand the scale of experimentation.

---

# 78. MULTIPLE TESTING

Every:

```text
portfolio configuration
optimizer configuration
alpha-weight configuration
constraint configuration
```

that is tested must be traceable.

Do not report the best configuration as though it were the only one tested.

---

# 79. RESEARCH GATE

Prompt 07 cannot replace Prompt 05.

The flow remains:

```text
Portfolio Construction
       ↓
Backtest
       ↓
Prompt 05 Validation
       ↓
Research Integrity
       ↓
Research Gate
```

Possible final status remains controlled by the existing gate.

No new live status.

---

# 80. SYNTHETIC DATA

Synthetic data may test:

```text
portfolio mathematics
optimizer correctness
constraint handling
risk calculations
alpha combination
known covariance structures
```

But:

```text
synthetic portfolio performance ≠ market evidence
```

Synthetic results must remain ineligible for:

```text
RESEARCH_CANDIDATE
PROMOTED_TO_PAPER
```

unless the existing policy explicitly changes in a later version.

Do NOT change that policy in Prompt 07.

---

# 81. SYNTHETIC KNOWN-ALPHA TEST

Create deterministic data where:

```text
Alpha A predicts returns
Alpha B is independent
Alpha C is negatively correlated
```

Verify that:

```text
ensemble construction
```

behaves mathematically as expected.

---

# 82. SYNTHETIC CORRELATION TEST

Create known covariance/correlation structures.

Verify:

```text
estimated correlation
covariance
risk contribution
```

within appropriate numerical tolerance.

---

# 83. CONSTRAINT TESTS

Test:

```text
max position
gross exposure
net exposure
sector limits
turnover limits
```

with deterministic examples.

---

# 84. INFEASIBILITY TESTS

Construct intentionally impossible constraints.

Expected:

```text
explicit INFEASIBLE result
```

Never silent relaxation.

---

# 85. OPTIMIZER TESTS

For small deterministic problems, compare optimizer results against analytically known or independently verified solutions where practical.

Do not rely solely on:

```text
solver returned success
```

---

# 86. COVARIANCE TESTS

Verify:

```text
symmetry
PSD behavior
dimension consistency
alignment by security_id
PIT window
```

---

# 87. TURNOVER TESTS

Manually verify:

```text
pretrade → target
```

turnover calculation.

---

# 88. EXPOSURE TESTS

Verify:

```text
gross
net
beta
sector
factor
```

where supported.

---

# 89. PORTFOLIO LEAKAGE TESTS

Create adversarial cases where:

```text
future return
future covariance
future sector
future universe
future volatility
```

could affect portfolio weights.

The integrity layer must detect/flag the leakage.

---

# 90. LOOK-AHEAD TEST

A historical target portfolio must not change merely because future bars are appended.

This should become a regression test.

---

# 91. DETERMINISM

Same:

```text
dataset snapshot
alpha versions
portfolio config
seed
code version
```

must produce the same target weights within documented numerical tolerance.

---

# 92. SECURITY ALIGNMENT

Never align arrays by:

```text
ticker string only
```

Use:

```text
security_id
decision_time
```

as the primary keys.

---

# 93. DATA ALIGNMENT

Before optimization verify:

```text
alpha values
risk values
covariance
constraints
universe
```

all refer to the same:

```text
decision_time
security set
```

---

# 94. MISSING ALPHA

If an alpha is missing for a security:

```text
do not silently substitute zero
```

Use an explicit policy:

```text
exclude
neutralize
missing
```

and record it.

---

# 95. MISSING RISK DATA

If covariance/volatility/beta data is missing:

```text
NOT_TESTED
```

or explicit exclusion.

Do not fabricate risk estimates.

---

# 96. NUMERICAL STABILITY

Portfolio optimizers must detect:

```text
NaN
Inf
singular matrices
ill-conditioned matrices
negative variance
invalid weights
```

and fail safely.

---

# 97. WEIGHT VALIDATION

Before returning target weights verify:

```text
finite
within constraints
correct security IDs
sum constraints
gross/net constraints
no accidental leverage
```

---

# 98. PORTFOLIO SANITY CHECK

Every target portfolio should produce diagnostics:

```text
number of positions
gross exposure
net exposure
cash
max weight
turnover
concentration
estimated volatility
```

---

# 99. PORTFOLIO REPORT

Create a machine-readable and human-readable research report.

Conceptually:

```text
QUANT LAB PORTFOLIO RESEARCH REPORT
===================================

Portfolio:
Version:

Dataset:
Snapshot:
Universe:

ALPHA ENSEMBLE
--------------
Components:
Weights:
Correlation:

CONSTRUCTION
------------
Method:
Objective:
Constraints:

RISK
----
Volatility:
Gross:
Net:
Beta:
Concentration:
Top-10:

TURNOVER
--------
Average:
Maximum:

COST
----
Commission:
Slippage:
Estimated impact:

VALIDATION
----------
OOS:
Walk-forward:
Robustness:
Statistics:

INTEGRITY
---------
PIT:
Universe:
Leakage:
Costs:

RESEARCH GATE
-------------
Status:
Warnings:
Reasons:
```

---

# 100. CLI

Extend the existing CLI rather than creating a new CLI framework.

Conceptual commands:

```text
quantlab portfolio list

quantlab portfolio inspect <id>

quantlab portfolio build <ensemble>

quantlab portfolio risk <experiment>

quantlab portfolio exposures <experiment>

quantlab portfolio turnover <experiment>

quantlab portfolio compare <a> <b>

quantlab research ensemble <id>

quantlab research portfolio <id>

quantlab research alpha-correlation <experiment>
```

Use the repository's actual command conventions.

---

# 101. DESKTOP

Extend the existing desktop through:

```text
quantlab.app
```

not directly from Qt to the data layer.

Potential views:

```text
Alpha Ensemble
Portfolio Lab
Portfolio Weights
Risk
Exposure
Correlation
Turnover
Optimization
Attribution
```

The UI is a client.

It must not:

```text
query Parquet directly
calculate portfolio weights independently
bypass risk
modify the ledger
promote research
execute orders
```

---

# 102. PORTFOLIO VISUALIZATION DATA

Prepare application-level results for:

```text
weight distribution
cumulative portfolio return
drawdown
turnover
risk contribution
alpha contribution
sector exposure
factor exposure
alpha correlation
```

Do not implement UI-only calculations.

---

# 103. PERFORMANCE

Use existing:

```text
DuckDB
Parquet
NumPy
Pandas
```

or the repository's established stack.

Do not introduce distributed compute infrastructure.

Optimize only after correctness.

---

# 104. CACHING

Portfolio results may be cached.

Cache identity must include:

```text
dataset snapshot
universe
alpha versions
ensemble configuration
optimizer
constraints
risk model
rebalance schedule
```

Never reuse incompatible weights.

---

# 105. RESEARCH PROVENANCE

Every optimizer result must answer:

```text
What alphas produced these weights?

What data snapshot was used?

What universe was used?

What covariance model was used?

What constraints were active?

What parameters were used?

Was optimization trained or fixed?

Was this OOS?

What costs were assumed?
```

---

# 106. NO BLACK-BOX OPTIMIZATION

Do not add:

```text
magic_optimizer()
```

Every optimizer must declare:

```text
objective
variables
constraints
solver
tolerances
initialization where relevant
```

---

# 107. SOLVER FAILURE

If an optimizer fails:

```text
FAIL
```

with:

```text
reason
solver status
diagnostics
```

Do not silently fall back to an unrelated portfolio.

If a documented deterministic fallback exists, record it explicitly.

---

# 108. BASELINE COMPARISON

Every sophisticated portfolio constructor should be benchmarkable against:

```text
equal weight
top-N equal weight
simple rank weighting
```

This is essential for determining whether optimization adds value.

---

# 109. OPTIMIZATION VALUE TEST

Ask:

```text
Does optimization improve OOS risk-adjusted performance
after costs relative to a transparent baseline?
```

If not:

```text
optimization failed to add evidence
```

That is a valid result.

---

# 110. PORTFOLIO TURNOVER VS ALPHA DECAY

Prepare analysis connecting:

```text
alpha decay
```

with:

```text
rebalance frequency
turnover
cost
```

Do not optimize this relationship using the final test set.

---

# 111. PORTFOLIO CAPACITY

Prepare a future interface for:

```text
capital
ADV
participation
impact
```

Do not manufacture capacity numbers.

---

# 112. FACTOR NEUTRALITY

Prepare a clean abstraction:

```text
Portfolio
    ↓
Factor exposure
    ↓
Constraint
```

This will later support:

```text
market-neutral
sector-neutral
beta-neutral
factor-neutral
```

strategies.

---

# 113. ALPHA ORTHOGONALIZATION

Integrate with Prompt 06's feature/alpha framework.

If an alpha is orthogonalized:

```text
parent alpha
reference factor
residual alpha
```

must be preserved in lineage.

Do not overwrite the original alpha.

---

# 114. ENSEMBLE VERSIONING

If:

```text
weights change
```

or:

```text
components change
```

create:

```text
new ensemble version
```

Do not mutate historical research.

---

# 115. PORTFOLIO VERSIONING

If:

```text
optimizer changes
constraints change
risk target changes
alpha ensemble changes
```

create a new portfolio model version.

---

# 116. EXPERIMENT IMMUTABILITY

Historical experiment records must not be rewritten to make a later portfolio look cleaner.

Corrections should create:

```text
new experiment/version
```

with lineage.

---

# 117. RESEARCH COMPARISON

Provide comparison at the experiment level:

```text
Portfolio A
Portfolio B
```

with common:

```text
dataset
universe
cost
validation
```

and differences explicitly displayed.

---

# 118. MULTIPLE TESTING + PORTFOLIO SEARCH

The research system must make visible:

```text
number of alpha combinations
number of portfolio configurations
number of optimizers
number of constraints tested
number of parameter sets
```

Prompt 05 remains responsible for formal multiple-testing corrections/gating.

---

# 119. STATISTICAL VS ECONOMIC SIGNIFICANCE

Report separately:

```text
statistical evidence
```

and:

```text
economic evidence
```

A portfolio can have:

```text
statistical evidence but poor economics
```

or:

```text
good historical economics but weak statistical evidence
```

Do not merge them.

---

# 120. RISK MODEL VS ALPHA MODEL

Keep separate:

```text
Alpha Model
```

and:

```text
Risk Model
```

The risk model must not secretly encode the alpha.

---

# 121. RISK MODEL LINEAGE

Record:

```text
risk inputs
window
estimator
normalization
PIT snapshot
```

---

# 122. PORTFOLIO OBJECT MODEL

The exact implementation is repository-dependent, but the conceptual model should resemble:

```text
PortfolioModel
    │
    ├── AlphaEnsemble
    │      ├── Alpha A
    │      ├── Alpha B
    │      └── Alpha C
    │
    ├── RiskModel
    │      ├── volatility
    │      ├── covariance
    │      └── exposures
    │
    ├── ConstraintSet
    │
    ├── Optimizer
    │
    └── RebalancePolicy
```

---

# 123. DEPENDENCY DIRECTION

Maintain:

```text
data
 ↓
features / labels
 ↓
alpha
 ↓
portfolio / risk
 ↓
backtest
 ↓
validation
 ↓
research
 ↓
app
 ↓
ui
```

Adapt to existing architecture where already established.

Avoid circular imports.

---

# 124. TEST MATRIX

Add tests across:

```text
alpha alignment
ensemble mathematics
normalization
cross-sectional ranking
alpha correlation
covariance
risk contribution
portfolio weights
constraints
long-only
long-short
turnover
concentration
beta
sector
factor
optimizer
infeasibility
PIT
look-ahead
lineage
versioning
caching
ledger
CLI
desktop boundaries
```

---

# 125. PROPERTY TESTING

Where appropriate verify:

```text
weights remain finite
hard constraints remain satisfied
rank transformations preserve ordering
equal-weight portfolio sums correctly
long-only weights never become negative
gross/net exposure equations hold
turnover is non-negative
risk is non-negative
```

---

# 126. ADVERSARIAL TESTING

Intentionally test:

```text
NaN alpha
Inf alpha
missing security
duplicate security
future covariance
future sector
future universe
singular covariance
infeasible constraints
extreme score
zero volatility
zero liquidity
```

The system must fail or handle them explicitly.

---

# 127. REPRODUCIBILITY TEST

Run the same portfolio experiment twice.

Expected:

```text
same configuration hash
same lineage
same target weights within tolerance
```

---

# 128. DESKTOP SMOKE TEST

Existing GUI tests must remain passing.

New views must operate through:

```text
quantlab.app
```

and must not import:

```text
PySide6
```

into domain/research code.

---

# 129. CLI SMOKE TEST

Verify commands actually execute against the same application services used by the desktop.

No duplicate business logic in CLI.

---

# 130. DOCUMENTATION

Create/update documentation under the existing structure.

Potential documents:

```text
docs/architecture/CROSS_SECTIONAL_ALPHA.md
docs/architecture/PORTFOLIO_CONSTRUCTION.md
docs/architecture/RISK_MODEL.md
docs/architecture/PORTFOLIO_CONSTRAINTS.md
docs/research/ALPHA_ENSEMBLE_PROTOCOL.md
docs/research/PORTFOLIO_RESEARCH_PROTOCOL.md
```

Do not create duplicates if equivalent documents already exist.

---

# 131. ADR

Inspect existing ADR numbering first.

Create ADRs only for genuine architectural decisions.

Potential decisions:

```text
alpha ensemble representation
portfolio target abstraction
constraint engine
risk model boundary
optimizer interface
```

Do not duplicate existing decisions.

---

# 132. OBSERVABILITY

Research runs should expose:

```text
experiment ID
portfolio ID
dataset snapshot
universe
optimizer status
constraint status
risk status
integrity status
```

Errors should be actionable.

---

# 133. ERROR TAXONOMY

Use existing exception conventions where possible.

Conceptual categories:

```text
PortfolioConfigurationError
ConstraintViolation
InfeasiblePortfolio
RiskModelError
CovarianceError
PITViolation
AlignmentError
OptimizationError
```

Do not create unnecessary duplicate exception systems.

---

# 134. SAFETY

Prompt 07 must preserve:

```text
LIVE_TRADING=false
```

No broker imports into:

```text
features
alpha
portfolio
risk
research
```

No Zerodha/Kite execution.

No OpenAlgo execution.

No order submission.

---

# 135. AI SAFETY

AI may eventually:

```text
suggest alpha combinations
suggest portfolio configurations
compare experiments
explain results
```

AI may NOT:

```text
override risk
override integrity
modify historical experiments
force portfolio weights
request live order
enable live trading
```

Any future AI interface must remain downstream of explicit research controls.

---

# 136. NO AUTOMATIC PROMOTION

The portfolio engine must not contain:

```text
promote_to_live()
```

or equivalent.

The maximum research state remains governed by the existing research gate.

---

# 137. NO BROKER LOGIC

Do not introduce:

```text
Zerodha
Kite
OpenAlgo
broker order API
```

into Prompt 07.

Execution remains a later phase.

---

# 138. PERFORMANCE TARGET

The first implementation should prioritize:

```text
correctness
```

over:

```text
optimizer speed
```

Do not add GPU/distributed systems.

---

# 139. IMPLEMENTATION ORDER

Implement in this sequence:

```text
1. Repository reconnaissance
2. Domain model reconciliation
3. Alpha ensemble abstraction
4. Cross-sectional alignment
5. Portfolio target abstraction
6. Baseline portfolio constructors
7. Constraint engine
8. Risk/covariance interface
9. Basic optimizers
10. Portfolio diagnostics
11. Attribution
12. Experiment/lineage integration
13. Prompt 05 validation integration
14. CLI
15. Desktop viewer
16. Tests
17. Documentation
18. Full regression
```

Do not jump directly to sophisticated optimization.

---

# 140. BASELINE-FIRST REQUIREMENT

Before implementing complex optimizers, ensure these work:

```text
top-N equal weight
bottom-N equal weight
rank-weighted
equal-weight ensemble
```

These are the control experiments.

---

# 141. OPTIMIZER-FIRST-PRINCIPLE

Every optimizer must answer:

```text
What does this add compared with the transparent baseline?
```

If it does not add robust OOS value:

```text
do not promote it
```

---

# 142. RESEARCH OUTPUT

At the end of Prompt 07, QUANT LAB should be able to perform:

```text
               ALPHA LIBRARY
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
   Momentum       Reversal      Volatility
       │             │             │
       └─────────────┼─────────────┘
                     ▼
               Alpha Ensemble
                     │
                     ▼
          Cross-sectional Scores
                     │
                     ▼
             Portfolio Builder
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
   Constraints      Risk       Turnover
       │             │             │
       └─────────────┼─────────────┘
                     ▼
               Target Weights
                     │
                     ▼
              Existing Backtest
                     │
                     ▼
             Prompt 05 Validation
                     │
                     ▼
                Research Gate
```

---

# 143. ACCEPTANCE CRITERIA

Prompt 07 is complete only when:

```text
✓ Prompts 01–06 remain intact.
✓ Existing PIT fabric remains authoritative.
✓ Existing backtester remains authoritative.
✓ Existing validation engine remains authoritative.
✓ Existing research gate remains authoritative.
✓ Existing experiment ledger remains authoritative.

✓ Cross-sectional alpha model exists.
✓ PIT universe alignment exists.
✓ Alpha normalization is explicit.
✓ Alpha sign convention exists.
✓ Alpha ensemble is versioned.
✓ Ensemble lineage exists.
✓ Alpha correlation analysis exists.
✓ Incremental alpha contribution analysis exists.

✓ Portfolio target abstraction exists.
✓ Target weights are distinct from orders.
✓ Long-only baseline exists.
✓ Long-short baseline exists where supported.
✓ Top-N portfolio exists.
✓ Rank-weighted portfolio exists.
✓ Equal-weight ensemble exists.

✓ Portfolio constraints exist.
✓ Hard vs soft constraints are explicit.
✓ Infeasible constraints fail explicitly.
✓ Position caps exist.
✓ Gross/net exposure controls exist.
✓ Concentration diagnostics exist.
✓ Turnover calculation exists.
✓ Turnover constraints are supported where appropriate.

✓ Risk model boundary exists.
✓ Covariance interface exists.
✓ Covariance PIT semantics exist.
✓ Covariance numerical validation exists.
✓ Risk contribution diagnostics exist.
✓ Volatility targeting architecture exists.

✓ Beta exposure is supported where data exists.
✓ Sector exposure is supported where PIT data exists.
✓ Factor exposure architecture exists.
✓ Missing unsupported data remains NOT_TESTED.

✓ Transparent baseline comparison exists.
✓ Optimizer interface exists.
✓ Minimum-variance architecture exists.
✓ Mean-variance architecture exists or is cleanly staged.
✓ Risk-parity architecture exists or is cleanly staged.
✓ Optimizer configuration is versioned.
✓ Optimizer search history is traceable.

✓ Portfolio experiments integrate with Prompt 05.
✓ Walk-forward optimization can be represented.
✓ OOS configuration is frozen correctly.
✓ Multiple-testing metadata is preserved.
✓ Synthetic results cannot be promoted.
✓ Integrity failures cannot become successful results.

✓ Feature/alpha/portfolio/strategy boundaries remain clean.
✓ No broker execution is introduced.
✓ LIVE_TRADING remains false.
✓ AI cannot bypass controls.

✓ CLI integration exists.
✓ Desktop integration uses quantlab.app.
✓ UI does not calculate research independently.
✓ Documentation is updated.
✓ ADRs are updated only where required.
✓ Full regression tests pass.
✓ ruff is clean.
✓ mypy --strict is clean.
✓ Existing `quantlab slice` remains functional.
✓ Existing `quantlab backtest` remains functional.
✓ Existing `quantlab validate` remains functional.
✓ Existing `quantlab research` remains functional.
```

---

# 144. CRITICAL INVARIANTS

## INVARIANT 1 — PIT

```text
weights(T) may depend only on information available by T
```

## INVARIANT 2 — UNIVERSE

```text
Universe(T) is historical
```

## INVARIANT 3 — TARGET ≠ ORDER

```text
target_weight != order
```

## INVARIANT 4 — ALPHA ≠ PORTFOLIO

A predictive signal is not automatically a portfolio.

## INVARIANT 5 — RISK ≠ ALPHA

Risk models must not secretly contain future return information.

## INVARIANT 6 — OPTIMIZATION ≠ VALIDATION

A successful optimizer solve does not imply a successful research result.

## INVARIANT 7 — HARD CONSTRAINTS

Hard constraints cannot be silently relaxed.

## INVARIANT 8 — MULTIPLE TESTING

Portfolio search history must remain visible.

## INVARIANT 9 — REPRODUCIBILITY

Same inputs/configuration produce reproducible weights.

## INVARIANT 10 — UNKNOWN

```text
NOT_TESTED != PASS
```

## INVARIANT 11 — SYNTHETIC

```text
synthetic evidence != market evidence
```

## INVARIANT 12 — LIVE

```text
LIVE_TRADING=false
```

## INVARIANT 13 — AI

```text
AI cannot override research/risk/live safety
```

---

# 145. WHAT NOT TO BUILD

Do NOT implement in Prompt 07:

```text
live trading
Zerodha execution
OpenAlgo execution
broker connectivity
autonomous AI trading
LLM stock selection
reinforcement learning
deep-learning portfolio optimizer
HFT
market making
order-book execution
distributed optimization cluster
```

These belong to later phases.

---

# 146. FINAL ENGINEERING DIRECTIVE

Do not build:

> "an optimizer that finds the highest-return portfolio."

Build:

> **a scientific portfolio-construction laboratory that determines whether combining predictive signals creates robust, diversified, economically viable portfolios after risk, turnover, costs, constraints, and out-of-sample validation.**

The fundamental research chain must remain:

```text
FEATURE
   ↓
ALPHA
   ↓
ALPHA ENSEMBLE
   ↓
PORTFOLIO
   ↓
RISK
   ↓
EXECUTION SIMULATION
   ↓
VALIDATION
   ↓
RESEARCH GATE
```

The laboratory must be able to answer:

```text
Which alphas were combined?

Why were they combined?

How correlated are they?

What incremental information does each provide?

What universe was used?

What information was available at T?

How were scores normalized?

How were weights generated?

Which constraints were active?

What risk model was used?

What covariance estimate was used?

What was the turnover?

What costs were assumed?

What exposures were created?

What happened out of sample?

Did optimization actually improve over a simple baseline?

How many configurations were tested?

Was the result robust?

What does the integrity engine say?

Why was the portfolio accepted or rejected?
```

The objective is **not maximum mathematical complexity**.

The objective is a portfolio-construction layer in which every decision is:

```text
explicit
mathematical
PIT-valid
versioned
traceable
reproducible
testable
economically interpretable
```

Build Prompt 07 on top of the existing **QUANT LAB 0.6.0** architecture.

**Do not reset. Do not duplicate. Do not bypass. Extend the laboratory.**
