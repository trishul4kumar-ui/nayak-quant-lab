# QUANT LAB — CURSOR MASTER PROMPT 08
# QUANTITATIVE RISK & FACTOR RESEARCH ENGINE

**Version:** 0.8  
**Project:** QUANT LAB  
**Mission:** Extend QUANT LAB 0.7 into a research-grade quantitative risk and factor research engine without breaking the existing PIT data fabric, alpha engine, portfolio constructor, backtester, validation engine, research gate, experiment ledger, application layer, or live-trading safety boundary.

---

## 0. ABSOLUTE DIRECTIVE

You are continuing the **existing QUANT LAB repository**.

**DO NOT RESET THE REPOSITORY.**  
**DO NOT rewrite Prompts 01–07.**  
**DO NOT create parallel implementations.**

Prompt 08 must extend the existing architecture.

Before modifying code:

```text
INSPECT
→ MAP
→ RECONCILE
→ DESIGN
→ IMPLEMENT
→ TEST
→ REGRESSION
→ DOCUMENT
```

Search the repository before assuming an abstraction is missing.

Preserve all existing invariants:

```text
PIT available_time <= decision_time
historical universe(T)
next-bar execution
10 bps default transaction costs
risk firewall
Research Integrity Engine
experiment ledger
reproducibility
NOT_TESTED != PASS
synthetic evidence != market evidence
LIVE_TRADING=false
AI cannot request live orders
desktop is a client of quantlab.app
```

---

# 1. CURRENT QUANT LAB BASELINE

Prompts 01–07 already establish:

```text
01  Core architecture
02  Quantitative research/backtest safety
03  Native desktop application
04  Point-in-Time Data Fabric
05  Research-Grade Backtesting & Validation
06  Feature & Alpha Research
07  Cross-Sectional Alpha & Portfolio Construction
```

Current research chain:

```text
PIT DATA
   ↓
FEATURE
   ↓
LABEL
   ↓
ALPHA
   ↓
ALPHA ENSEMBLE
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

Prompt 08 adds:

```text
QUANTITATIVE RISK
FACTOR RESEARCH
FACTOR EXPOSURE
RISK ATTRIBUTION
FACTOR MODELING
PORTFOLIO RISK DECOMPOSITION
STRESS TESTING
```

Target architecture:

```text
                     PIT DATA FABRIC
                            │
          ┌─────────────────┴─────────────────┐
          ▼                                   ▼
      FEATURES                            MARKET STATE
          │
          ▼
       ALPHAS
          │
          ▼
    ALPHA ENSEMBLES
          │
      ┌───┴──────────────┐
      ▼                  ▼
 FACTOR ENGINE       RISK ENGINE
      │                  │
      │          ┌───────┼────────┐
      │          ▼       ▼        ▼
      │      Covariance Beta   Exposure
      │          │       │        │
      └──────────┼───────┼────────┘
                 ▼
       PORTFOLIO CONSTRUCTION
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
     WEIGHTS    RISK   CONSTRAINTS
        │        │        │
        └────────┼────────┘
                 ▼
            RISK FIREWALL
                 │
                 ▼
             BACKTEST
                 │
                 ▼
          VALIDATION ENGINE
                 │
                 ▼
            RESEARCH GATE
                 │
                 ▼
          EXPERIMENT LEDGER
```

---

# 2. PRIMARY RESEARCH QUESTION

Prompt 08 must answer:

> **What risks are embedded in an alpha or portfolio, where do those risks come from, how stable are they through time, and does apparent alpha survive after controlling for systematic risk exposures?**

A positive return is not automatically alpha.

A strategy can contain:

```text
market beta
sector concentration
size exposure
momentum exposure
value exposure
quality exposure
volatility exposure
liquidity exposure
correlation risk
```

The system must distinguish:

```text
ALPHA
RISK EXPOSURE
FACTOR RETURN
SYSTEMATIC RETURN
IDIOSYNCRATIC RETURN
```

---

# 3. FUNDAMENTAL DOMAIN SEPARATION

Maintain:

```text
FEATURE ≠ FACTOR ≠ ALPHA ≠ RISK MODEL ≠ PORTFOLIO
```

Specifically:

- A feature is an information transformation.
- A factor is an economically meaningful systematic dimension.
- An alpha is a predictive signal.
- A risk model estimates uncertainty/exposure.
- A portfolio converts alpha into positions/weights.

Do not collapse these domains.

---

# 4. RISK MODEL ≠ ALPHA MODEL

This is a critical architectural invariant.

```text
ALPHA MODEL
    ↓
expected-return information

RISK MODEL
    ↓
variance / covariance / exposure information
```

The risk model must not secretly encode future returns.

---

# 5. FACTOR MODEL

Prepare architecture for the standard factor representation:

```text
R = B F + ε
```

where:

```text
R = asset returns
B = factor exposure matrix
F = factor returns
ε = idiosyncratic component
```

This is a model, not an assumption that all returns are perfectly explained.

Keep:

```text
factor exposure
factor return
residual return
```

as separate objects.

---

# 6. VERSIONED FACTOR DEFINITION

Create or extend a versioned factor abstraction.

Conceptually:

```text
FactorDefinition
├── factor_id
├── version
├── name
├── category
├── definition
├── formula
├── inputs
├── normalization
├── winsorization
├── expected_direction
├── frequency
├── PIT requirements
└── lineage
```

Do not duplicate an existing definition.

---

# 7. FACTOR TAXONOMY

Support the architecture for:

```text
MARKET
STYLE
SECTOR
MACRO
LIQUIDITY
VOLATILITY
MICROSTRUCTURE
CUSTOM
```

Implement only factors supported by actual available data.

---

# 8. FACTOR VERSIONING

Any change to:

```text
formula
inputs
lookback
normalization
winsorization
universe
sector definition
```

must create a new version.

Historical experiments remain immutable.

---

# 9. PIT FACTOR COMPUTATION

Every factor value at time T must use:

```text
available_time <= T
```

for every input.

This includes:

```text
prices
fundamentals
market cap
sector
index membership
corporate actions
shares outstanding
beta
volatility
liquidity
```

No current labels may be backfilled into historical factor values unless their historical availability time is known.

---

# 10. FACTOR PROVENANCE

Every factor result should expose:

```text
dataset_id
snapshot_id
security_id
decision_time
input_features
input_versions
```

The system must answer:

> What information produced this factor value?

---

# 11. FACTOR PIPELINE

Use:

```text
PIT DATA
   ↓
VALIDATED INPUTS
   ↓
RAW FACTOR
   ↓
MISSING-DATA POLICY
   ↓
OUTLIER POLICY
   ↓
CROSS-SECTIONAL NORMALIZATION
   ↓
FACTOR SCORE
```

All transformations must be explicit.

---

# 12. CROSS-SECTIONAL NORMALIZATION

Support explicit:

```text
rank
percentile
z-score
robust z-score
winsorized z-score
```

For z-score:

```text
z_i = (x_i - μ) / σ
```

where `μ` and `σ` are computed only from the PIT-valid cross-section at T.

---

# 13. OUTLIER HANDLING

Support explicit winsorization.

Record:

```text
lower percentile
upper percentile
method
```

Never silently winsorize.

---

# 14. FACTOR NEUTRALIZATION

Prepare architecture for:

```text
raw factor
    ↓
control for market / size / sector / other factors
    ↓
residual factor
```

The residual factor must have a new identity/version.

Never overwrite the source factor.

---

# 15. FACTOR ORTHOGONALIZATION

Prepare explicit methods such as:

```text
cross-sectional regression residual
factor residualization
Gram-Schmidt-style orthogonalization
```

Do not claim economic independence merely because statistical correlation is low.

---

# 16. FACTOR EXPOSURE

For a portfolio:

```text
Exposure_f = Σ_i w_i × f_i
```

where:

```text
w_i = portfolio weight
f_i = PIT-valid factor exposure
```

The convention must be documented.

---

# 17. FACTOR EXPOSURE MATRIX

Support a structure equivalent to:

```text
                     MARKET   SIZE   MOMENTUM   VALUE
Security A             0.9    -0.2      1.1      0.4
Security B             1.1     0.3      0.2     -0.7
Security C             0.8     0.1     -0.9      1.2
```

Primary key:

```text
security_id + decision_time
```

not ticker position.

---

# 18. MARKET BETA

Implement a beta research interface.

Conceptually:

```text
β_i = Cov(R_i, R_m) / Var(R_m)
```

Requirements:

```text
PIT-valid observations
explicit lookback
explicit frequency
explicit benchmark
explicit return definition
minimum observations
```

Do not invent NIFTY returns.

If a valid benchmark is unavailable:

```text
NOT_TESTED
```

---

# 19. BETA STABILITY

Measure:

```text
rolling beta
mean
standard deviation
range
regime changes
```

Do not assume beta is stationary.

---

# 20. SECTOR EXPOSURE

Where PIT sector data exists:

```text
SectorWeight_s = Σ_{i∈s} w_i
```

Track:

```text
sector weights
largest sector
top sectors
sector HHI
active sector weights
```

Do not use today's sector classification historically.

---

# 21. SIZE FACTOR

Prepare architecture for PIT market capitalization:

```text
size = log(market_cap)
```

with explicit normalization.

No fabricated market-cap data.

---

# 22. VALUE FACTOR

Prepare architecture for:

```text
book-to-market
earnings yield
cash-flow yield
```

Only implement when real PIT fundamentals exist.

---

# 23. QUALITY FACTOR

Prepare architecture for:

```text
ROE
ROA
profitability
earnings stability
leverage quality
```

Do not fabricate fundamentals.

---

# 24. VOLATILITY FACTOR

Reuse Prompt 06 feature infrastructure where possible.

Potential measures:

```text
realized volatility
downside volatility
idiosyncratic volatility
```

Do not duplicate feature calculations.

---

# 25. LIQUIDITY FACTOR

Prepare architecture for:

```text
ADV
turnover
volume
spread
Amihud-style measures
```

If real liquidity data is unavailable:

```text
NOT_TESTED
```

Never fabricate ADV.

---

# 26. FACTOR ≠ FACTOR RETURN

Distinguish:

```text
factor exposure
```

from:

```text
factor return
```

A factor portfolio return is not the same object as a security's factor exposure.

---

# 27. FACTOR PORTFOLIOS

Where appropriate, prepare transparent factor portfolios:

```text
rank
→ long-short
→ equal weight
```

Do not automatically treat factor portfolios as investable products.

---

# 28. FACTOR IC

Reuse Prompt 06 IC infrastructure.

Do not create a second IC engine.

Factor IC remains research evidence, not automatic promotion.

---

# 29. FACTOR CORRELATION

Distinguish:

```text
factor-score correlation
```

from:

```text
factor-return correlation
```

Report methodology and window.

---

# 30. ASSET COVARIANCE

Extend Prompt 07 covariance infrastructure.

Requirements:

```text
PIT-valid returns
security alignment
lookback
frequency
missing-data policy
estimator
PSD validation
```

Do not create a second covariance engine.

---

# 31. COVARIANCE ESTIMATORS

Establish an extensible interface for:

```text
sample covariance
EWMA covariance
shrinkage covariance
robust covariance
```

Implement a small baseline first.

Do not implement every estimator just for feature count.

---

# 32. COVARIANCE PIT SEMANTICS

At decision time T:

```text
Σ(T)
```

may only use returns available by T.

Appending future observations must not change historical:

```text
Σ(T)
```

---

# 33. COVARIANCE NUMERICAL VALIDATION

Validate:

```text
symmetry
positive-semidefinite behavior
eigenvalues
condition number
rank
dimension
security alignment
```

Invalid matrices must fail explicitly.

---

# 34. PSD REPAIR

If a matrix requires repair:

```text
detect
record
apply an explicit documented repair
```

Never silently alter covariance.

---

# 35. COVARIANCE STABILITY

Report:

```text
condition number
effective rank
smallest eigenvalue
largest eigenvalue
```

where applicable.

---

# 36. FACTOR COVARIANCE

Prepare architecture for:

```text
Ω = Cov(F)
```

where factor returns exist.

Do not assume factor covariance equals asset covariance.

---

# 37. FACTOR MODEL ESTIMATION

Separate:

```text
factor exposures B
factor returns F
residual ε
```

with independent lineage.

---

# 38. REGRESSION MODEL

Prepare:

```text
r_i,t = α_i + β_i^T F_t + ε_i,t
```

using only valid historical observations.

---

# 39. REGRESSION OUTPUT

Record:

```text
coefficient
standard error
t-statistic
p-value
R²
observations
window
factor set
estimator
```

Do not report coefficients without sample definition.

---

# 40. ROBUST REGRESSION

Prepare architecture for:

```text
heteroskedasticity-robust
HAC / Newey-West
clustered
```

Implement only where justified.

Never silently switch estimators.

---

# 41. REGRESSION INTERCEPT

If a regression produces:

```text
α
```

label it as:

```text
model intercept estimate
```

Do not automatically call it genuine alpha.

Send it through Prompt 05 for formal validation.

---

# 42. IDIOSYNCRATIC RETURN

Where a factor model exists:

```text
ε_i,t = R_i,t - B_i,t F_t
```

must be traceable.

Residual return is not automatically predictive alpha.

---

# 43. PORTFOLIO FACTOR EXPOSURE

For portfolio weights:

```text
B_p = wᵀB
```

with explicit dimension/orientation.

Report:

```text
market beta
size
value
momentum
quality
volatility
sector
custom factors
```

where available.

---

# 44. ACTIVE EXPOSURE

Where a valid benchmark exists:

```text
w_active = w_portfolio - w_benchmark
```

and:

```text
factor_active = Bᵀ w_active
```

No benchmark →:

```text
NOT_AVAILABLE
```

---

# 45. TRACKING ERROR

Where benchmark data exists:

```text
TE = std(R_p - R_b)
```

with explicit:

```text
frequency
annualization
window
```

No valid benchmark → `NOT_AVAILABLE`.

---

# 46. PORTFOLIO RISK DECOMPOSITION

Prepare the factor-model representation:

```text
Σ = B Ω Bᵀ + D
```

where:

```text
B = factor exposures
Ω = factor covariance
D = idiosyncratic covariance
```

Only use this decomposition when the underlying model/data supports it.

---

# 47. FACTOR RISK CONTRIBUTION

Report, where valid:

```text
factor
exposure
variance contribution
risk contribution
```

Document the methodology.

---

# 48. IDIOSYNCRATIC RISK

Report residual/idiosyncratic risk where:

```text
D
```

is available.

Do not force a decomposition if the model cannot support it.

---

# 49. RISK RECONCILIATION

Where exact factor decomposition is supported:

```text
total modeled risk
≈
factor risk + idiosyncratic risk
```

within documented numerical tolerance.

Otherwise:

```text
NOT_AVAILABLE
```

---

# 50. ASSET RISK CONTRIBUTION

Reuse Prompt 07's risk framework.

Conceptually:

```text
RC_i = w_i × (Σw)_i / σ_p
```

with:

```text
σ_p = sqrt(wᵀΣw)
```

Handle:

```text
zero volatility
negative numerical variance
NaN
Inf
```

safely.

---

# 51. MARGINAL CONTRIBUTION TO RISK

Prepare:

```text
MCR_i = (Σw)_i / σ_p
```

with explicit zero-risk handling.

---

# 52. RISK BUDGETING

Integrate with Prompt 07.

Prepare:

```text
asset risk budget
factor risk budget
sector risk budget
```

Risk budgets must be explicit.

---

# 53. RISK CONSTRAINTS

Extend the existing Prompt 07 constraint engine.

Potential constraints:

```text
max beta
min beta
beta neutrality
sector cap
sector neutrality
factor exposure range
factor neutrality
max volatility
max concentration
max factor risk contribution
```

Hard constraints remain hard.

---

# 54. INFEASIBILITY

If:

```text
alpha objective
+
portfolio constraints
+
risk constraints
```

are infeasible:

```text
INFEASIBLE
```

Do not silently relax constraints.

---

# 55. FACTOR-NEUTRAL PORTFOLIO

Prepare architecture for:

```text
maximize alpha
subject to:
    Bᵀw ≈ target_exposure
```

where B is PIT-valid.

---

# 56. MARKET-NEUTRAL PORTFOLIO

Prepare:

```text
β_portfolio ≈ 0
```

only when valid beta data exists.

---

# 57. SECTOR-NEUTRAL PORTFOLIO

Prepare:

```text
sector exposure ≈ benchmark
```

only when historical sector and benchmark data exist.

---

# 58. FACTOR-CONTROLLED ALPHA

A major research workflow:

```text
RAW ALPHA
   ↓
MEASURE FACTOR EXPOSURES
   ↓
RESIDUALIZE / CONTROL
   ↓
RESIDUAL ALPHA
   ↓
IC / QUANTILES
   ↓
PORTFOLIO
   ↓
OOS VALIDATION
```

Residual alpha must be a new versioned alpha.

---

# 59. FACTOR CROWDING

Prepare diagnostics for:

```text
common factor exposure
portfolio concentration
alpha-factor overlap
```

Do not claim market-wide crowding without appropriate external data.

---

# 60. FACTOR STABILITY

Measure through time:

```text
rolling exposure
mean
standard deviation
max/min
regime stability
```

---

# 61. RISK REGIMES

Reuse existing regime infrastructure.

Potential regimes:

```text
high volatility
low volatility
high correlation
low correlation
high dispersion
low dispersion
bull
bear
stress
```

Do not create a second regime engine.

---

# 62. DISPERSION

Where valid data exists, expose:

```text
cross-sectional return dispersion
```

as a market-state diagnostic.

Do not confuse dispersion with volatility.

---

# 63. STRESS TESTING

Prepare explicit scenario infrastructure.

Examples:

```text
market shock
volatility shock
sector shock
factor shock
correlation increase
liquidity deterioration
```

Scenarios are hypothetical analyses, not forecasts.

---

# 64. HISTORICAL STRESS

Where sufficient real data exists, support historical stress-period analysis.

Do not fabricate historical stress data.

---

# 65. PARAMETRIC STRESS

Prepare:

```text
factor shock
volatility shock
correlation shock
```

with explicit assumptions.

---

# 66. STRESS OUTPUT

Record:

```text
scenario
shock
portfolio P&L impact
factor contribution
largest affected positions
constraint status
```

---

# 67. FACTOR RESEARCH REPORT

Create/update a machine-readable and human-readable report:

```text
FACTOR RESEARCH REPORT
======================

Factor:
Version:
Definition:

Inputs:
Dataset:
Snapshot:
Universe:
As-of:

PIT STATUS:
Coverage:
Missing %:
Outlier %:

Normalization:
Winsorization:

IC:
Rank IC:
IC volatility:
IC hit rate:
IC decay:

Factor Correlation:
Factor Return Correlation:

Exposure:
Stability:

Risk Contribution:

Residualized Result:

Limitations:

Validation:
Research Gate:
```

---

# 68. RISK REPORT

Extend Prompt 07's portfolio report:

```text
QUANT LAB RISK REPORT
=====================

Portfolio:
Version:
Experiment:

DATA
----
Dataset:
Snapshot:
Universe:
As-of:

RISK MODEL
----------
Estimator:
Window:
Frequency:
Covariance:
Factor Model:

PORTFOLIO RISK
--------------
Volatility:
Gross:
Net:
Max Weight:
Concentration:
Turnover:

FACTOR EXPOSURE
---------------
Market:
Size:
Value:
Momentum:
Quality:
Volatility:
Sector:
Custom:

RISK CONTRIBUTION
-----------------
Factor:
Idiosyncratic:
Largest Asset:
Largest Factor:

STABILITY
---------
Beta:
Factor Exposure:
Correlation Regime:

STRESS
------
Scenario:
Impact:

INTEGRITY
---------
PIT:
Alignment:
Leakage:
Data Quality:

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

# 69. RISK MODEL IDENTITY

Create or extend:

```text
RiskModel
├── risk_model_id
├── version
├── covariance_estimator
├── factor_set
├── factor_versions
├── lookback
├── frequency
├── benchmark
├── missing_data_policy
├── normalization
└── configuration_hash
```

Historical risk models remain immutable.

---

# 70. RISK MODEL LINEAGE

Every risk result must identify:

```text
dataset snapshot
factor versions
return window
covariance estimator
benchmark
configuration
code version
```

---

# 71. COVARIANCE CACHE

Reuse Prompt 07 caching.

Cache identity must include:

```text
dataset snapshot
security set
as_of
lookback
frequency
estimator
factor versions
risk configuration
```

---

# 72. SECURITY ALIGNMENT

Never align:

```text
returns
weights
factor exposures
```

by ticker position.

Use:

```text
security_id
decision_time
```

---

# 73. MISSING DATA

Default:

```text
missing != zero
```

Allowed explicit policies:

```text
exclude
neutralize
not_available
```

Record the selected policy.

---

# 74. SURVIVORSHIP

Factor and risk calculations must use historical:

```text
Universe(T)
```

where available.

Do not use today's survivors.

---

# 75. CORPORATE ACTIONS

Reuse the existing PIT/corporate-action policy.

Unknown historical announcement timing remains:

```text
NOT_TESTED
```

where applicable.

---

# 76. FACTOR QUALITY

Every factor should report:

```text
coverage
missing %
outlier %
cross-sectional dispersion
effective N
```

---

# 77. SMALL CROSS-SECTIONS

Define a minimum valid cross-sectional sample size.

If insufficient:

```text
NOT_AVAILABLE
```

Do not generate unstable statistics.

---

# 78. FACTOR CORRELATION MATRIX

Produce:

```text
F × F
```

with:

```text
factor IDs
versions
window
method
```

---

# 79. PCA

Prepare architecture for PCA diagnostics on:

```text
factor exposures
return covariance
```

where scientifically appropriate.

PCA components are statistical components, not automatically economic factors.

---

# 80. EIGENVALUE ANALYSIS

Where appropriate report:

```text
eigenvalues
condition number
effective rank
```

---

# 81. RISK CONCENTRATION

Distinguish:

```text
weight concentration
```

from:

```text
risk concentration
```

Report:

```text
top risk contributors
factor risk concentration
sector risk concentration
```

---

# 82. RISK-ADJUSTED ALPHA

Where a valid factor model exists, support diagnostic comparison:

```text
raw portfolio return
− factor-explained component
=
residual return
```

This is diagnostic.

Formal statistical validation remains Prompt 05.

---

# 83. ALPHA RESIDUALIZATION

Integrate with Prompt 06.

Example:

```text
momentum alpha
    ↓
control for market + size + sector
    ↓
residual momentum alpha
```

Never overwrite the original alpha.

---

# 84. FACTOR TIMING

Do not implement automatic factor timing based on future returns.

Any future timing model must pass:

```text
PIT
walk-forward
multiple testing
OOS validation
```

through Prompt 05.

---

# 85. MACHINE LEARNING BOUNDARY

Do not build an ML risk model in Prompt 08.

Prepare clean interfaces so future models can plug into:

```text
RiskModel
FactorModel
CovarianceEstimator
```

without changing domain boundaries.

---

# 86. NO LLM RISK DECISIONS

AI/LLM components may eventually explain results or propose research hypotheses.

They may NOT:

```text
override risk
override integrity
override constraints
modify historical results
approve portfolios
request live orders
enable live trading
```

---

# 87. NO LIVE TRADING

Prompt 08 must introduce:

```text
NO broker connectivity
NO Zerodha/Kite execution
NO OpenAlgo execution
NO order submission
```

Preserve:

```text
LIVE_TRADING=false
```

---

# 88. APPLICATION BOUNDARY

Maintain domain/application separation.

The architecture must remain equivalent to:

```text
quantlab.data
quantlab.features
quantlab.labels
quantlab.alpha
quantlab.portfolio
quantlab.risk
quantlab.backtest
quantlab.validation
quantlab.research
quantlab.app
quantlab.ui
```

Adapt names to the existing repository.

No circular dependencies.

---

# 89. DESKTOP RISK LAB

Extend through:

```text
quantlab.app
```

Potential views:

```text
Risk Lab
Factor Lab
Exposure
Covariance
Correlation
Attribution
Stress Test
Risk Diagnostics
```

UI must not:

```text
read Parquet directly
calculate covariance independently
modify risk limits
rewrite ledger records
bypass research gate
```

---

# 90. CLI

Extend the existing CLI.

Potential commands:

```text
quantlab risk list
quantlab risk inspect <id>
quantlab risk compute <portfolio>
quantlab risk exposure <portfolio>
quantlab risk attribution <experiment>
quantlab risk covariance <experiment>
quantlab risk stress <experiment>

quantlab factor list
quantlab factor inspect <id>
quantlab factor compute <id>
quantlab factor exposure <portfolio>

quantlab research factor <id>
quantlab research factor-correlation <id>
```

Use actual repository conventions.

Do not create a second CLI framework.

---

# 91. EXPERIMENT LEDGER

Use the existing ledger.

Record:

```text
risk_model_id
risk_model_version
factor_set
factor_versions
dataset_id
snapshot_id
universe_id
portfolio_id
portfolio_version
configuration_hash
```

---

# 92. MULTIPLE TESTING

Risk research also creates search multiplicity.

Record:

```text
factor sets tested
lookbacks tested
covariance estimators tested
risk constraints tested
factor combinations tested
stress scenarios tested
```

Prompt 05 remains authoritative for formal statistical correction/gating.

---

# 93. BASELINE-FIRST IMPLEMENTATION

Start with transparent baselines:

```text
simple rolling volatility
sample covariance
simple beta
simple factor exposure
simple factor portfolio
```

Then add sophistication only where useful.

---

# 94. RISK MODEL ROBUSTNESS

Compare:

```text
sample covariance
vs
EWMA
vs
shrinkage
```

only where implemented and meaningful.

Use identical:

```text
dataset
universe
period
portfolio
cost assumptions
```

for fair comparison.

---

# 95. FACTOR MODEL ROBUSTNESS

Compare factor specifications without mutating historical experiments.

Example:

```text
market-only
market + size
market + size + value + momentum
```

Each is a distinct model configuration.

---

# 96. MULTICOLLINEARITY

For regression/factor models detect:

```text
high factor correlation
condition number
VIF
```

where appropriate.

Do not interpret unstable coefficients blindly.

---

# 97. FACTOR DOCUMENTATION

Every implemented factor must document:

```text
Definition
Economic intuition
Formula
Inputs
Lookback
Normalization
Outlier policy
Missing-data policy
PIT requirements
Known limitations
```

---

# 98. PORTFOLIO BEFORE/AFTER RISK CONTROL

Compare:

```text
raw alpha portfolio
vs
risk-controlled portfolio
```

using:

```text
return
volatility
Sharpe
drawdown
turnover
factor exposure
factor risk
OOS stability
```

Prompt 05 remains responsible for formal validation.

---

# 99. RISK MODEL VALUE TEST

A key experiment:

> Does the risk model improve portfolio robustness without manufacturing an apparent improvement through hidden future information?

This must be testable.

---

# 100. OPTIMIZER BOUNDARY

Prompt 07's optimizer may consume:

```text
covariance
factor exposures
risk targets
```

but Prompt 08 must not turn the risk package into the portfolio optimizer.

Maintain:

```text
RiskModel → PortfolioConstructor
```

not:

```text
RiskModel = PortfolioOptimizer
```

---

# 101. TEST MATRIX

Add tests for:

```text
factor identity
factor versioning
PIT factor calculation
normalization
winsorization
factor coverage
factor correlation
factor exposure
beta
sector exposure
covariance
PSD validation
condition number
risk contribution
factor decomposition
idiosyncratic risk
factor neutrality
constraint enforcement
stress scenarios
regression
residualization
lineage
caching
CLI
desktop boundaries
```

---

# 102. ADVERSARIAL TESTS

Test:

```text
NaN factor
Inf factor
future factor
future covariance
future beta
future sector
future universe
singular covariance
near-singular covariance
constant factor
zero variance
empty universe
duplicate security
misaligned factor matrix
```

---

# 103. LOOK-AHEAD TEST

Append future data after T.

Expected:

```text
factor(T) unchanged
beta(T) unchanged
covariance(T) unchanged
risk_model(T) unchanged
portfolio_weights(T) unchanged
```

This is mandatory.

---

# 104. FUTURE FACTOR LEAKAGE TEST

Create a deliberately leaking factor.

Expected:

```text
integrity FAIL
```

or the established explicit leakage status.

---

# 105. FUTURE COVARIANCE TEST

Append future observations.

Expected:

```text
Σ(T)
```

does not change.

---

# 106. FUTURE UNIVERSE TEST

Changing future membership must not change historical factor/risk results.

---

# 107. LABEL LEAKAGE TEST

Factor inputs cannot use:

```text
forward return
future drawdown
future volatility
```

The integrity layer must reject/flag this.

---

# 108. NUMERICAL EDGE CASES

Test:

```text
zero volatility
negative numerical variance
NaN
Inf
single security
two securities
singular matrix
near-singular matrix
constant factor
empty cross-section
```

---

# 109. REPRODUCIBILITY

Same:

```text
snapshot
factor set
risk configuration
portfolio
seed
code version
```

must produce the same result within documented tolerance.

---

# 110. PERFORMANCE

Correctness first.

Do not introduce:

```text
GPU
distributed cluster
Spark
Ray
Kubernetes
```

for Prompt 08.

Use the established local-first stack.

---

# 111. OBSERVABILITY

Expose:

```text
risk model
factor set
covariance status
condition number
factor count
asset count
missing %
constraint status
integrity status
```

---

# 112. FAILURE MODES

Explicit failure for:

```text
invalid covariance
insufficient observations
invalid factor matrix
NaN
Inf
alignment mismatch
PIT violation
infeasible constraints
```

No silent fallback.

---

# 113. FORBIDDEN SILENT FALLBACKS

Do NOT do:

```text
covariance failure → identity matrix
beta failure → zero
missing factor → zero
missing sector → ignore constraint
missing benchmark → fabricate benchmark
```

unless the repository already has an explicit documented policy.

---

# 114. FACTOR EXPOSURE UNKNOWN

Never confuse:

```text
true zero
```

with:

```text
unknown
```

---

# 115. RISK MODEL UNKNOWN

If required risk inputs are unavailable:

```text
NOT_TESTED
```

or:

```text
UNEVALUABLE
```

not:

```text
PASS
```

---

# 116. RESEARCH HYPOTHESES

The engine should support experiments such as:

```text
H1:
Momentum alpha survives market-beta control.

H2:
Momentum alpha survives sector neutralization.

H3:
Momentum alpha survives market + size + value controls.

H4:
Combining momentum and low-volatility reduces portfolio risk
without destroying OOS alpha.

H5:
Shrinkage covariance produces more stable portfolio risk
than sample covariance.

H6:
Risk-neutralized alpha is more robust OOS than raw alpha.

H7:
Portfolio optimization adds value beyond transparent equal-weight
and rank-weighted baselines.
```

These are hypotheses, not assumptions.

---

# 117. FACTOR-ALPHA RESEARCH MATRIX

Support research such as:

```text
                  RAW        BETA CONTROL    SECTOR CONTROL
Momentum           ✓              ✓                ✓
Value              ✓              ✓                ✓
Quality            ✓              ✓                ✓
Volatility         ✓              ✓                ✓
```

Each cell is a distinct experiment.

---

# 118. FACTOR-ALPHA ORTHOGONALITY

Measure:

```text
score correlation
regression exposure
incremental IC
```

Do not equate low correlation with economic independence.

---

# 119. RISK-CONTROL COMPARISON

Compare:

```text
raw portfolio
vs
beta-neutral portfolio
vs
sector-neutral portfolio
vs
factor-neutral portfolio
```

using the same:

```text
PIT data
universe
backtester
cost model
validation protocol
```

unless explicitly changed.

---

# 120. FACTOR TIMING SAFETY

Any future factor timing capability must remain subject to:

```text
PIT
walk-forward
OOS
multiple-testing control
research gate
```

---

# 121. DOCUMENTATION

Inspect existing documentation before creating files.

Potential additions:

```text
docs/architecture/RISK_ENGINE.md
docs/architecture/FACTOR_ENGINE.md
docs/architecture/FACTOR_MODEL.md
docs/research/RISK_RESEARCH_PROTOCOL.md
docs/research/FACTOR_RESEARCH_PROTOCOL.md
```

Do not create duplicates.

---

# 122. ADR

Inspect existing ADR numbering first.

Create ADRs only for genuine architectural decisions.

Potential subjects:

```text
risk-model boundary
factor-model boundary
factor exposure representation
covariance estimator interface
risk attribution
stress testing
```

Do not duplicate existing decisions.

---

# 123. ACCEPTANCE CRITERIA

Prompt 08 is complete only when:

```text
✓ Prompts 01–07 remain intact.
✓ Existing PIT fabric remains authoritative.
✓ Existing Feature Engine remains authoritative.
✓ Existing Alpha Engine remains authoritative.
✓ Existing Portfolio Engine remains authoritative.
✓ Existing Backtester remains authoritative.
✓ Existing Validation Engine remains authoritative.
✓ Existing Research Gate remains authoritative.
✓ Existing Experiment Ledger remains authoritative.

✓ Versioned FactorDefinition exists.
✓ Factor lineage exists.
✓ PIT factor computation exists.
✓ Explicit normalization exists.
✓ Explicit missing-data policy exists.
✓ Factor quality diagnostics exist.
✓ Factor correlation exists.
✓ Factor exposure exists.

✓ Market beta interface exists.
✓ Beta uses PIT-valid observations.
✓ Sector exposure exists where data exists.
✓ Size architecture exists where data exists.
✓ Value architecture exists where data exists.
✓ Quality architecture exists where data exists.
✓ Volatility factor architecture exists.
✓ Liquidity remains NOT_TESTED when unavailable.

✓ Asset covariance uses PIT returns.
✓ Covariance estimator is versioned.
✓ PSD validation exists.
✓ Numerical diagnostics exist.
✓ Condition number/eigen diagnostics exist.
✓ Covariance cache identity is correct.

✓ RiskModel abstraction exists.
✓ FactorModel abstraction exists where appropriate.
✓ Asset risk contribution exists.
✓ Factor risk contribution architecture exists.
✓ Idiosyncratic risk architecture exists.

✓ Risk constraints integrate with Prompt 07.
✓ Hard constraints remain hard.
✓ Infeasible constraints fail explicitly.
✓ Missing risk data is never silently zeroed.

✓ Factor neutralization integrates with Prompt 06.
✓ Original factors/alphas remain immutable.
✓ Residualized factors/alphas have independent identity and lineage.

✓ Stress testing infrastructure exists.
✓ Stress scenarios are explicit.
✓ Stress results are not forecasts.

✓ Prompt 05 validation remains authoritative.
✓ Prompt 05 research gate remains authoritative.
✓ Multiple-testing metadata is preserved.
✓ Synthetic results cannot be promoted.

✓ Future-data leakage tests exist.
✓ Future covariance test exists.
✓ Future factor test exists.
✓ Future universe test exists.
✓ Reproducibility tests exist.
✓ Numerical edge-case tests exist.

✓ CLI integrates through existing application services.
✓ Desktop integrates through quantlab.app.
✓ UI does not calculate risk independently.
✓ No broker execution is introduced.
✓ LIVE_TRADING remains false.
✓ AI cannot override risk or integrity.

✓ Existing slice works.
✓ Existing backtest works.
✓ Existing validate works.
✓ Existing research works.
✓ Existing portfolio workflows work.
✓ Full pytest passes.
✓ ruff clean.
✓ mypy --strict clean.
```

---

# 124. CRITICAL INVARIANTS

## INVARIANT 1 — PIT

```text
Risk(T) depends only on information available by T.
```

## INVARIANT 2 — HISTORICAL UNIVERSE

```text
Universe(T), not today's surviving universe.
```

## INVARIANT 3 — RISK ≠ ALPHA

Risk inputs cannot secretly encode future returns.

## INVARIANT 4 — FACTOR ≠ ALPHA

Factor exposure is not automatically predictive alpha.

## INVARIANT 5 — FACTOR ≠ FEATURE

Economic factor definitions remain distinct from generic features.

## INVARIANT 6 — TARGET ≠ ORDER

Risk-adjusted target weights remain research objects, not orders.

## INVARIANT 7 — MISSING ≠ ZERO

Unknown information cannot become an artificial zero.

## INVARIANT 8 — HARD CONSTRAINTS

Hard constraints cannot be silently relaxed.

## INVARIANT 9 — ONE CANONICAL ENGINE

Do not create parallel:

```text
data fabric
covariance engine
backtester
validation engine
ledger
risk firewall
```

## INVARIANT 10 — UNKNOWN

```text
NOT_TESTED != PASS
```

## INVARIANT 11 — SYNTHETIC

```text
synthetic evidence != market evidence
```

## INVARIANT 12 — REPRODUCIBILITY

Same snapshot + configuration produces reproducible results.

## INVARIANT 13 — LIVE

```text
LIVE_TRADING=false
```

## INVARIANT 14 — AI

```text
AI cannot override risk,
integrity,
research gate,
or live safety.
```

---

# 125. WHAT NOT TO BUILD

Do NOT implement in Prompt 08:

```text
live trading
Zerodha/Kite execution
OpenAlgo execution
broker connectivity
autonomous trading
LLM portfolio decisions
reinforcement learning
deep-learning risk models
HFT
market making
order-book execution
live risk management
```

Those belong to later phases.

---

# 126. FINAL TARGET

After Prompt 08, QUANT LAB should be capable of answering:

```text
WHAT DID THE PORTFOLIO EARN?
        ↓
WHAT RISK DID IT TAKE?
        ↓
WHICH FACTORS EXPLAINED THAT RISK?
        ↓
HOW STABLE WERE THOSE EXPOSURES?
        ↓
HOW MUCH WAS SYSTEMATIC?
        ↓
HOW MUCH WAS IDIOSYNCRATIC?
        ↓
DID THE ALPHA SURVIVE FACTOR CONTROLS?
        ↓
DID IT SURVIVE OOS VALIDATION?
        ↓
DID IT SURVIVE COSTS?
        ↓
DID THE RISK MODEL REMAIN STABLE?
        ↓
DID THE RESULT BEAT TRANSPARENT BASELINES?
        ↓
WHAT DOES THE INTEGRITY ENGINE SAY?
        ↓
WHAT DOES THE RESEARCH GATE SAY?
```

The goal is **not** maximum mathematical complexity.

The goal is:

```text
discover
→ measure
→ decompose
→ control
→ validate
→ falsify
```

A result such as:

```text
"Momentum disappeared after beta/sector control."
```

is a successful research outcome.

A result such as:

```text
"Momentum survived market, size and sector controls."
```

is also a successful research outcome.

A result such as:

```text
"Shrinkage covariance did not improve OOS robustness."
```

is a successful research outcome.

QUANT LAB must be engineered to discover what is true, not to manufacture attractive backtests.

---

# 127. FINAL ENGINEERING DIRECTIVE

Build Prompt 08 as a **scientific quantitative risk and factor research laboratory**.

The final chain is:

```text
PIT DATA
   ↓
FEATURES
   ↓
ALPHA
   ↓
FACTOR RESEARCH
   ↓
RISK MODEL
   ↓
PORTFOLIO CONSTRUCTION
   ↓
RISK ATTRIBUTION
   ↓
STRESS TESTING
   ↓
BACKTEST
   ↓
OOS VALIDATION
   ↓
RESEARCH GATE
   ↓
EXPERIMENT LEDGER
```

Every material decision must remain:

```text
explicit
mathematical
PIT-valid
versioned
traceable
reproducible
testable
economically interpretable
falsifiable
```

**Do not reset QUANT LAB 0.7.0.**

**Do not duplicate existing engines.**

**Do not bypass the PIT fabric.**

**Do not bypass the risk firewall.**

**Do not bypass Prompt 05 validation.**

**Do not introduce live execution.**

**Extend the laboratory.**
