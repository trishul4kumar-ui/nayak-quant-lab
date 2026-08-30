# QUANT LAB — CURSOR MASTER PROMPT 06
# FEATURE & ALPHA RESEARCH ENGINE

**Version:** 0.6  
**Date:** 2026-08-30  
**Project:** QUANT LAB  
**Mission:** Build a rigorous, point-in-time-correct Feature & Alpha Research Engine on top of the existing QUANT LAB 0.5 research and validation infrastructure.

---

# 0. EXECUTION DIRECTIVE

You are continuing the **existing QUANT LAB repository**.

## NON-NEGOTIABLE

**DO NOT RESET THE REPOSITORY.**

**DO NOT REWRITE Prompts 01–05.**

**DO NOT create a second data fabric, second backtester, or second validation engine.**

Prompt 06 must extend the existing architecture.

Preserve all existing guarantees:

```text
PIT available_time <= decision_time
next-bar execution
10 bps default transaction costs
risk firewall
Research Integrity Engine
experiment ledger
lineage
reproducibility
LIVE_TRADING=false
AI cannot request live orders
desktop is a client of quantlab.app
synthetic data cannot become market evidence
NOT_TESTED never becomes PASS
```

Before changing code:

```text
INSPECT → MAP EXISTING ARCHITECTURE → RECONCILE → IMPLEMENT → TEST → DOCUMENT
```

Do not assume the architecture described below exactly matches the repository. Inspect the actual repository first and extend the existing abstractions wherever possible.

---

# 1. PURPOSE

QUANT LAB now has:

```text
Prompt 01  Architecture
Prompt 02  Quantitative Core + Safety
Prompt 03  Desktop Application
Prompt 04  Point-in-Time Data Fabric
Prompt 05  Research-Grade Backtesting & Validation
```

Prompt 06 creates the next major layer:

> **FEATURE & ALPHA RESEARCH ENGINE**

The purpose is NOT to create an indicator library.

The purpose is to build a scientific research environment capable of answering:

> **Does a measurable, economically meaningful, temporally valid relationship exist between information available at time T and future market behavior?**

The engine must support:

```text
hypothesis
   ↓
feature definition
   ↓
PIT feature computation
   ↓
cross-sectional / time-series analysis
   ↓
forward-label analysis
   ↓
IC / predictive-power analysis
   ↓
signal decay
   ↓
portfolio simulation
   ↓
Prompt 05 validation
   ↓
research gate
   ↓
experiment ledger
```

---

# 2. CORE PHILOSOPHY

Do not optimize for:

```text
number of indicators
number of strategies
highest in-sample Sharpe
highest backtest return
```

Optimize for:

```text
scientific validity
mathematical clarity
falsifiability
reproducibility
temporal correctness
economic interpretation
robustness
low redundancy
out-of-sample evidence
```

A feature that has no predictive information is a valid research result.

A feature that works only because of look-ahead is a failed experiment.

A feature that works only under one arbitrary parameter is fragile.

A feature discovered after thousands of unrecorded trials must not be treated as a clean hypothesis.

---

# 3. CRITICAL DISTINCTION

The system must distinguish:

```text
FEATURE
```

from:

```text
SIGNAL
```

from:

```text
ALPHA
```

from:

```text
STRATEGY
```

from:

```text
PORTFOLIO
```

Conceptually:

```text
RAW DATA
   ↓
FEATURE
   ↓
PREDICTIVE RELATIONSHIP
   ↓
ALPHA SIGNAL
   ↓
PORTFOLIO CONSTRUCTION
   ↓
EXECUTABLE STRATEGY
```

Do not collapse these layers into one Python function.

---

# 4. TARGET ARCHITECTURE

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
    PIT Store         Feature Registry       PySide6
        │                   │
        ▼                   ▼
   MarketState        Feature Engine
                            │
                ┌───────────┼───────────┐
                ▼           ▼           ▼
             Feature      Alpha       Labels
              Store       Tests
                │           │           │
                └───────────┼───────────┘
                            ▼
                    Research Experiments
                            │
                            ▼
                    Prompt 05 Validation
                            │
                            ▼
                    Research Integrity
                            │
                            ▼
                     Experiment Ledger
```

There must be ONE canonical path through the research infrastructure.

---

# 5. FIRST TASK — REPOSITORY RECONNAISSANCE

Before implementing anything inspect:

```text
src/quantlab/
tests/
docs/
configs/
results/
CLI
desktop/application services
MarketState
PIT provider
backtester
validation engine
research ledger
integrity engine
strategy abstractions
existing momentum feature
```

Determine:

```text
what is already implemented
what is duplicated
what should be extended
what should be refactored
what should remain untouched
```

Do not create duplicate abstractions merely because this prompt names one.

---

# 6. FEATURE AS A FIRST-CLASS RESEARCH OBJECT

Create or extend a typed feature abstraction.

Conceptually:

```python
FeatureDefinition(
    feature_id=...,
    version=...,
    name=...,
    description=...,
    mathematical_definition=...,
    inputs=...,
    lookback=...,
    horizon=...,
    frequency=...,
    timestamp_semantics=...,
    availability_semantics=...,
    universe_requirements=...,
    normalization=...,
    missing_value_policy=...,
    implementation_version=...,
)
```

The exact API is an engineering decision.

A feature must have an immutable identity/version.

---

# 7. FEATURE IDENTITY

A feature identity must capture the things that affect its meaning.

At minimum consider:

```text
feature_id
feature_version
formula
inputs
lookback
sampling frequency
normalization
winsorization
missing-value policy
universe
```

If the mathematical definition changes:

```text
new feature version
```

Do not silently overwrite previous definitions.

---

# 8. MATHEMATICAL DEFINITION

Every feature must have a human-readable mathematical definition.

Example:

```text
Momentum_N(t)
=
P(t) / P(t-N) - 1
```

or:

```text
z_t = (x_t - μ_t) / σ_t
```

The definition must identify:

```text
input variables
lookback
time reference
normalization
output
```

The code implementation must correspond to the documented mathematical definition.

---

# 9. TIMESTAMP SEMANTICS

Every feature must define:

```text
observation_time
available_time
decision_time
```

The feature engine must enforce:

```text
feature.available_time <= decision_time
```

The feature engine must NOT assume:

```text
event_time == available_time
```

---

# 10. POINT-IN-TIME FEATURE COMPUTATION

Features must be computed from the PIT data fabric.

Preferred flow:

```text
Feature Request(as_of=T)
        ↓
PIT Data Query
        ↓
Information available by T
        ↓
Feature computation
        ↓
Feature value
```

Never compute historical features using today's fully revised dataset unless the feature explicitly permits it.

---

# 11. NO FUTURE INFORMATION

Forbidden:

```text
close[t+1]
future volume
future universe membership
future corporate action
future fundamental revision
future normalization statistics
future ranking universe
future benchmark
```

unless the feature explicitly represents future labels, in which case it belongs to the **label engine**, not the feature engine.

---

# 12. FEATURE VS LABEL

Create a strict separation.

```text
FEATURE
available at T
```

versus:

```text
LABEL
defined using T+H or future observations
```

Example:

```text
momentum_20(T)
```

may be:

```text
P(T) / P(T-20) - 1
```

while:

```text
forward_return_5d(T)
```

is:

```text
P(T+5) / P(T) - 1
```

The latter must NEVER enter feature computation.

---

# 13. LABEL ENGINE

Create a reusable forward-label abstraction.

Conceptually:

```text
ForwardReturn(H)
ForwardExcessReturn(H)
ForwardVolatility(H)
ForwardDrawdown(H)
ForwardBinaryDirection(H)
```

The label engine must explicitly identify:

```text
label_time
horizon
end_time
```

and must interact correctly with Prompt 05 purge/embargo logic.

---

# 14. FEATURE CATEGORIES

Build an extensible taxonomy.

Initial categories:

```text
PRICE
VOLUME
VOLATILITY
MOMENTUM
MEAN_REVERSION
CROSS_SECTIONAL
MARKET_STRUCTURE
LIQUIDITY
SEASONALITY
REGIME
RELATIVE
STATISTICAL
```

Do not require every category to be populated in Prompt 06.

The taxonomy is an architectural framework.

---

# 15. INITIAL FEATURE SET

Implement a small, mathematically defensible seed library.

Do NOT build hundreds of technical indicators.

Start with high-information primitives.

Examples:

```text
1D return
5D return
10D return
20D return
60D return
120D return
252D return
rolling volatility
rolling mean
rolling standard deviation
z-score
high-low range
close-to-high
close-to-low
volume change
volume z-score
turnover proxy
rolling beta where data permits
cross-sectional rank
```

Only implement features for which the current data contract provides valid inputs.

---

# 16. MOMENTUM FAMILY

Formalize the existing momentum strategy as a feature family.

Examples:

```text
momentum_5
momentum_10
momentum_20
momentum_60
momentum_120
momentum_252
```

Avoid hardcoding:

```text
momentum_20
```

as the only momentum definition.

---

# 17. MEAN REVERSION FAMILY

Prepare features such as:

```text
short_term_return
distance_from_rolling_mean
rolling_zscore
short-term reversal
```

Definitions must be explicit.

---

# 18. VOLATILITY FAMILY

Prepare:

```text
realized_volatility
rolling_std
true_range
range_expansion
volatility_change
```

Do not introduce look-ahead through centered windows.

---

# 19. VOLUME FAMILY

Where valid data exists:

```text
volume_change
volume_zscore
relative_volume
rolling_volume
```

If reliable volume is unavailable:

```text
NOT_TESTED
```

Do not synthesize market volume and present it as real.

---

# 20. CROSS-SECTIONAL FEATURES

This is a major capability.

At decision time T:

```text
Universe(T)
     ↓
Feature values
     ↓
Cross-sectional ranking
     ↓
Percentile / z-score
```

The universe MUST itself be point-in-time correct.

Never rank against today's surviving universe for historical dates.

---

# 21. CROSS-SECTIONAL NORMALIZATION

Support:

```text
rank
percentile rank
z-score
robust z-score
winsorized z-score
```

Normalization must be configurable and recorded in feature identity.

---

# 22. NORMALIZATION LOOK-AHEAD

Critical invariant:

If normalization uses:

```text
mean(T)
std(T)
```

those values must be computed only from information legitimately available at T.

Never calculate:

```text
mean(all_history)
```

and apply it retrospectively without explicitly declaring the leakage.

---

# 23. WINSORIZATION

Prepare a winsorization transformation.

Example:

```text
lower percentile
upper percentile
```

But ensure thresholds are calculated from permissible information.

Record:

```text
method
threshold
scope
```

---

# 24. MISSING VALUES

Every feature must define:

```text
missing_value_policy
```

Possible policies:

```text
DROP
FORWARD_FILL
ZERO
NOT_AVAILABLE
```

Do not use zero as a universal missing-value replacement.

For financial quantities:

```text
missing ≠ zero
```

---

# 25. FEATURE QUALITY

Create feature-quality diagnostics.

At minimum:

```text
coverage
missingness
unique values
mean
std
min
max
quantiles
outlier rate
```

For cross-sectional features:

```text
cross-sectional coverage
```

---

# 26. FEATURE STABILITY

Evaluate feature distribution through time.

Report:

```text
mean by period
std by period
quantiles by period
missingness by period
```

A feature whose distribution changes dramatically should be flagged for investigation.

---

# 27. FEATURE CORRELATION

Implement correlation analysis.

Support:

```text
Pearson
Spearman
```

Where applicable.

The purpose is to identify:

```text
redundant features
```

not to maximize the number of uncorrelated indicators.

---

# 28. FEATURE REDUNDANCY

Prepare a redundancy graph/matrix.

Conceptually:

```text
Feature A ───── 0.92 ───── Feature B
Feature A ───── 0.10 ───── Feature C
```

This will later help construct compact alpha libraries.

---

# 29. FORWARD RETURN ANALYSIS

For each feature and horizon:

```text
feature(T)
      ↓
forward return(T+H)
```

Analyze:

```text
mean forward return
median forward return
volatility
hit rate
```

But do not interpret raw conditional return as proof of alpha.

---

# 30. INFORMATION COEFFICIENT

Implement:

```text
Pearson IC
Spearman Rank IC
```

For cross-sectional research:

```text
IC(T)
=
corr(feature(T), forward_return(T+H))
```

Record IC for each observation date.

---

# 31. IC SUMMARY

Calculate:

```text
IC mean
IC median
IC std
IC information ratio
IC hit rate
IC t-statistic where statistically appropriate
```

Avoid blindly treating daily IC observations as IID.

---

# 32. IC DECAY

Build:

```text
H = 1
H = 2
H = 5
H = 10
H = 20
H = 60
```

or configurable horizons.

Produce:

```text
IC(H)
```

This helps determine whether predictive information persists or decays rapidly.

---

# 33. SIGNAL DECAY

Separate:

```text
predictive decay
```

from:

```text
portfolio return decay
```

The feature engine should focus on predictive information.

Prompt 05 handles portfolio/backtest consequences.

---

# 34. QUANTILE ANALYSIS

Implement cross-sectional quantile analysis.

Example:

```text
Q1  lowest feature values
Q2
Q3
Q4
Q5  highest feature values
```

Measure forward returns by quantile.

Look for:

```text
monotonicity
```

not merely:

```text
Q5 > Q1
```

---

# 35. MONOTONICITY

A useful alpha relationship may look like:

```text
Q1  -0.20%
Q2  -0.05%
Q3   0.02%
Q4   0.10%
Q5   0.24%
```

This is generally more informative than:

```text
Q1 -0.20%
Q2  0.20%
Q3 -0.10%
Q4  0.10%
Q5  0.24%
```

Build diagnostics rather than relying on visual interpretation.

---

# 36. LONG-SHORT SPREAD

Where valid:

```text
Q_high return
-
Q_low return
```

Calculate:

```text
spread return
spread volatility
spread Sharpe
spread consistency
```

This is a research diagnostic, not automatic trade authorization.

---

# 37. FEATURE-PORTFOLIO BRIDGE

Provide a clean interface:

```text
Feature
  ↓
Signal transformation
  ↓
Portfolio construction
  ↓
Prompt 05 Backtester
```

Examples:

```text
rank
zscore
threshold
quantile
linear combination
```

Do not embed portfolio construction inside feature definitions.

---

# 38. ALPHA OBJECT

Create a first-class alpha abstraction.

Conceptually:

```text
AlphaDefinition
├── alpha_id
├── version
├── hypothesis_id
├── input_features
├── transformation
├── expected_direction
├── horizon
├── universe
├── normalization
├── mathematical_definition
├── implementation_version
└── lineage
```

---

# 39. ALPHA ≠ FEATURE

Example:

```text
Feature:
momentum_20
```

could become:

```text
Alpha:
rank(momentum_20)
```

or:

```text
Alpha:
zscore(momentum_20) - zscore(volatility_20)
```

These are distinct research objects.

---

# 40. ALPHA COMBINATIONS

Prepare the architecture for:

```text
linear combination
rank combination
weighted score
orthogonalized combination
```

Do not introduce large ML models yet.

Start with transparent mathematical combinations.

---

# 41. ORTHOGONALIZATION

Prepare for removing known feature exposure.

Example:

```text
Feature A
   ↓
regress against Feature B
   ↓
residual
```

The residual can be tested as a new research feature.

Statistical assumptions must be documented.

---

# 42. FACTOR / FEATURE NEUTRALITY

Prepare analysis for determining whether a candidate alpha is simply:

```text
momentum
value
size
volatility
market beta
sector exposure
```

Do not call something "new alpha" merely because it produces returns.

---

# 43. REGIME-CONDITIONAL ALPHA

Feature evaluation should eventually support:

```text
feature performance by regime
```

using Prompt 05's regime definitions.

Report:

```text
IC by regime
spread by regime
coverage by regime
```

---

# 44. SECTOR-CONDITIONAL ANALYSIS

Where sector classifications are available:

```text
feature IC by sector
feature return by sector
```

But sector data must be PIT-correct.

Do not use today's sector classifications historically.

---

# 45. MARKET-CAP CONDITIONAL ANALYSIS

Where market-cap data is available:

```text
large cap
mid cap
small cap
```

Again:

```text
market_cap(T)
```

must be available as-of T.

---

# 46. LIQUIDITY-CONDITIONAL ANALYSIS

Prepare:

```text
high liquidity
medium liquidity
low liquidity
```

but do not implement a fake liquidity model.

If ADV/spread data is missing:

```text
NOT_TESTED
```

---

# 47. FEATURE DECAY VS TURNOVER

The system should eventually connect:

```text
signal half-life
```

with:

```text
holding period
turnover
transaction costs
```

But do not optimize holding period on the final test set.

---

# 48. HYPOTHESIS REGISTRY INTEGRATION

Each research feature/alpha should be linked to a hypothesis.

Example:

```text
Hypothesis H-001
"Past medium-term relative strength predicts future cross-sectional returns."

        ↓

Feature F-001
momentum_20

        ↓

Alpha A-001
rank(momentum_20)

        ↓

Experiment E-001

        ↓

Validation
```

---

# 49. PRE-REGISTRATION SUPPORT

Prepare the architecture for:

```text
expected_direction
expected_horizon
expected_universe
expected_sign
expected_feature
```

A hypothesis may optionally be marked:

```text
PRE_REGISTERED
```

Do not pretend all current historical experiments were pre-registered.

---

# 50. MULTIPLE-TESTING INTEGRATION

Prompt 05 tracks multiple testing.

Prompt 06 must use it.

Every feature/alpha experiment should record:

```text
research_family_id
hypothesis_id
experiment_id
feature_id
alpha_id
parameter_set
number_of_prior_trials
```

If 500 variants were tested and one selected, the research record must preserve that fact.

---

# 51. FEATURE DISCOVERY REGISTRY

Create a searchable registry.

It should answer:

```text
What features exist?
Which versions exist?
What inputs do they use?
What datasets have they been tested on?
Which hypotheses generated them?
What experiments tested them?
What happened?
```

---

# 52. FEATURE STATUS

Suggested lifecycle:

```text
DRAFT
TESTING
SUPPORTED
REJECTED
FRAGILE
REDUNDANT
CONTAMINATED
DEPRECATED
```

Do not automatically label a feature:

```text
PROFITABLE
```

Profitability is not the correct scientific classification.

---

# 53. ALPHA STATUS

Suggested lifecycle:

```text
DRAFT
TESTING
SUPPORTED
REJECTED
FRAGILE
REDUNDANT
CONTAMINATED
RESEARCH_CANDIDATE
DEPRECATED
```

Promotion to:

```text
RESEARCH_CANDIDATE
```

must pass Prompt 05 research validation.

---

# 54. EXPERIMENT DESIGN

Provide a structured experiment configuration.

Conceptually:

```text
AlphaExperimentConfig
├── hypothesis
├── dataset
├── PIT snapshot
├── universe
├── feature set
├── label
├── horizons
├── normalization
├── evaluation method
├── train/test protocol
├── cost assumptions
├── random seed
└── validation protocol
```

---

# 55. RESEARCH EXPERIMENT PIPELINE

Implement:

```text
Experiment
   ↓
Resolve PIT dataset
   ↓
Resolve universe
   ↓
Compute feature
   ↓
Compute label
   ↓
Align timestamps
   ↓
Quality checks
   ↓
IC analysis
   ↓
Quantile analysis
   ↓
Decay analysis
   ↓
Optional portfolio bridge
   ↓
Prompt 05 validation
   ↓
Research gate
   ↓
Ledger
```

---

# 56. TIMESTAMP ALIGNMENT

This is critical.

For every feature/label pair verify:

```text
feature.available_time <= feature.decision_time
```

and:

```text
label_start > decision_time
```

according to the configured label convention.

Reject ambiguous timestamp alignment.

---

# 57. UNIVERSE ALIGNMENT

At every decision time:

```text
Universe(T)
```

must be resolved from the PIT universe service.

Do not use:

```text
current_universe
```

for historical experiments.

---

# 58. SURVIVORSHIP

The feature engine must respect the Prompt 04 survivorship status.

If historical membership/delistings are unavailable:

```text
survivorship = NOT_TESTED
```

Do not silently use today's survivors.

---

# 59. CORPORATE ACTIONS

Feature computation must respect the existing corporate-action policy.

Do not mix:

```text
raw price
adjusted price
split-adjusted price
total-return series
```

without explicit semantics.

---

# 60. PRICE SEMANTICS

Every feature based on price must declare which price field it uses.

Examples:

```text
open
high
low
close
adjusted_close
```

Do not silently substitute one for another.

---

# 61. ADJUSTMENT POLICY

Document whether a feature uses:

```text
unadjusted prices
split-adjusted prices
total-return adjusted prices
```

The choice must be reproducible.

---

# 62. CROSS-SECTIONAL DATE HANDLING

At each date:

```text
available instruments
        ↓
valid feature values
        ↓
valid labels
        ↓
intersection
        ↓
cross-sectional analysis
```

Record the number of observations.

Do not hide changing sample size.

---

# 63. MINIMUM SAMPLE SIZE

Statistical analyses should have configurable minimum sample sizes.

If insufficient:

```text
NOT_TESTED
```

not:

```text
PASS
```

---

# 64. OUTLIER HANDLING

Support explicit policies:

```text
none
winsorize
clip
robust transform
```

Every transformation must be recorded.

---

# 65. FEATURE QUALITY GATE

Before predictive analysis:

```text
coverage check
timestamp check
missingness check
variance check
outlier check
PIT check
```

If the feature is constant:

```text
REJECT / NOT_TESTED
```

as appropriate.

---

# 66. DATA SNOOPING

Do not allow the feature registry to erase failed feature experiments.

Historical experiments are part of the research record.

A researcher must be able to determine:

```text
what was tried
when
under which dataset
with which parameters
and why it failed
```

---

# 67. RESEARCH ARTIFACTS

A feature research experiment should produce machine-readable artifacts.

Conceptually:

```text
feature_experiment/
    config.json
    feature_definition.json
    label_definition.json
    feature_quality.json
    ic.json
    quantiles.json
    decay.json
    correlations.json
    validation.json
    integrity.json
    lineage.json
```

Follow the repository's existing artifact conventions if they differ.

---

# 68. CLI

Extend the existing CLI.

Conceptual commands:

```text
quantlab feature list
quantlab feature inspect <id>
quantlab feature compute <id>
quantlab feature quality <id>

quantlab alpha list
quantlab alpha inspect <id>

quantlab research feature <feature-id>
quantlab research alpha <alpha-id>

quantlab research ic <experiment-id>
quantlab research quantiles <experiment-id>
quantlab research decay <experiment-id>
quantlab research correlation <experiment-id>
```

Do not create a competing CLI framework.

---

# 69. DESKTOP INTEGRATION

Extend the desktop only through `quantlab.app`.

Possible views:

```text
Features
Alpha Lab
Feature Explorer
IC Analysis
Quantile Analysis
Decay
Feature Correlation
Research History
```

The UI must not:

```text
read Parquet directly
compute features independently
bypass PIT services
modify experiment records
promote alpha
```

---

# 70. FEATURE EXPLORER

The desktop should eventually allow a researcher to inspect:

```text
feature definition
formula
version
coverage
distribution
IC
decay
quantile returns
correlations
validation
lineage
```

Do not build a visually complex dashboard before the underlying application services exist.

---

# 71. PLOTTING

Prepare machine-readable data for:

```text
IC time series
IC decay
quantile return curves
feature distributions
correlation matrices
conditional performance
```

Plots must be generated from application/service results, not directly from raw storage in the UI.

---

# 72. STATISTICAL DISCIPLINE

Do not automatically interpret:

```text
IC > 0
```

as evidence of alpha.

Report:

```text
sample size
mean
dispersion
confidence interval where appropriate
statistical test
multiple-testing context
```

---

# 73. ECONOMIC SIGNIFICANCE

A statistically detectable feature may still be economically useless.

Always consider:

```text
turnover
costs
slippage
capacity
liquidity
```

Use Prompt 05 for economic validation.

---

# 74. FEATURE COMBINATION

Implement transparent combination methods first:

```text
equal-weight standardized features
weighted standardized features
rank average
rank sum
```

All weights must be explicit.

Do not optimize weights against the final test set.

---

# 75. FEATURE STANDARDIZATION

Support:

```text
cross-sectional z-score
time-series z-score
rank normalization
```

These are mathematically different.

Never label them generically as:

```text
normalize()
```

without recording the method.

---

# 76. TIME-SERIES VS CROSS-SECTIONAL

Explicitly distinguish:

```text
time-series feature
```

from:

```text
cross-sectional feature
```

Example:

```text
asset A momentum today
```

is a time-series computation.

Ranking all stocks today by momentum is:

```text
cross-sectional transformation
```

Keep these layers separate.

---

# 77. FEATURE OPERATORS

Prepare a composable operator framework.

Potential operators:

```text
lag
delta
return
rolling_mean
rolling_std
zscore
rank
percentile
winsorize
clip
difference
ratio
log
abs
sign
```

Operators must have explicit temporal semantics.

---

# 78. EXPRESSION ENGINE

Prepare for feature expressions such as:

```text
rank(momentum_20)
```

and:

```text
zscore(momentum_20) - zscore(volatility_20)
```

Do not use unrestricted Python evaluation.

If an expression language is implemented, it must be:

```text
typed
validated
sandboxed
deterministic
versioned
```

---

# 79. COMPUTATION GRAPH

A feature expression should eventually form a DAG:

```text
close
 │
 ├── return_20
 │
 └── volatility_20
        │
        ▼
 zscore(return_20)
        │
        └──────────────┐
                       ▼
              alpha_expression
```

This enables:

```text
lineage
caching
dependency analysis
reproducibility
```

---

# 80. FEATURE LINEAGE

Every computed feature must know:

```text
source columns
source dataset
snapshot
operators
parameters
versions
```

A feature result without lineage is not research-grade.

---

# 81. CACHING

Feature computations may be cached.

Cache key must include all meaningful inputs:

```text
dataset snapshot
feature version
operator versions
universe
time range
frequency
normalization
```

A stale or mismatched cache must never be reused.

---

# 82. PARALLELISM

Feature computation may eventually be parallelized.

But:

```text
correctness > speed
```

Parallel results must be deterministic where possible.

Do not introduce complex distributed infrastructure in Prompt 06.

---

# 83. COMPUTATIONAL PERFORMANCE

Use the existing:

```text
Parquet
DuckDB
NumPy/Pandas or repository-standard numerical tools
```

where appropriate.

Avoid loading an entire multi-year universe into memory if the data fabric supports efficient queries.

---

# 84. RESEARCH DATA SNAPSHOT

Every feature experiment must pin:

```text
dataset_id
dataset_version
snapshot_id
checksum
```

This is mandatory for reproducibility.

---

# 85. SYNTHETIC DATA

Synthetic data may be used to test:

```text
feature formulas
timestamp alignment
operator behavior
known mathematical relationships
```

But:

```text
synthetic predictive performance ≠ market evidence
```

Do not promote synthetic alpha.

---

# 86. KNOWN-SIGNAL SYNTHETIC TESTS

Create deterministic synthetic datasets where a known relationship exists.

Example:

```text
feature = x
future_return = 0.1*x + noise
```

The engine should detect the relationship.

Also create null datasets where:

```text
feature ⟂ future_return
```

The engine should not systematically report strong alpha.

This is an important test of the research machinery.

---

# 87. ADVERSARIAL LEAKAGE TESTS

Create synthetic tests where leakage is intentionally introduced.

Examples:

```text
feature contains future return
future normalization
future universe
future price
```

The integrity system must detect or flag them.

---

# 88. NULL FEATURE TESTS

Test:

```text
random feature
constant feature
permuted feature
```

Expected behavior:

```text
no reliable predictive relationship
```

subject to statistical uncertainty.

---

# 89. FEATURE STABILITY TESTS

Create deterministic tests for:

```text
same input → same feature
same snapshot → same result
changed feature version → changed identity
```

---

# 90. FEATURE MATHEMATICS TESTS

For each primitive feature verify against known formulas.

Example:

```text
momentum_20
```

must exactly match its mathematical definition.

Do not test only whether the code executes.

Test numerical correctness.

---

# 91. LABEL TESTS

Verify:

```text
forward_return_1d
forward_return_5d
forward_return_20d
```

against manually computed expected values.

---

# 92. CROSS-SECTIONAL TESTS

Verify:

```text
rank
percentile
zscore
```

against deterministic examples.

Handle ties explicitly and document the convention.

---

# 93. IC TESTS

Use deterministic data with known correlation.

Verify:

```text
Pearson IC
Spearman IC
```

against expected results.

---

# 94. QUANTILE TESTS

Use deterministic feature values:

```text
1
2
3
4
5
```

and verify quantile assignment and forward-return aggregation.

---

# 95. DECAY TESTS

Construct synthetic data where predictive power intentionally decays by horizon.

Verify the engine identifies:

```text
strong short horizon
weak long horizon
```

without leaking future data.

---

# 96. REDUNDANCY TESTS

Construct:

```text
Feature A = X
Feature B = X
```

and verify high correlation.

Also:

```text
Feature C = independent noise
```

and verify lower correlation subject to statistical uncertainty.

---

# 97. RESEARCH GATE INTEGRATION

Prompt 06 does not replace Prompt 05's gate.

The pipeline is:

```text
Feature/Alpha Research
        ↓
Prompt 05 Validation
        ↓
Research Integrity
        ↓
Research Gate
```

A strong IC alone cannot promote an alpha.

---

# 98. ALPHA PROMOTION

The maximum result from Prompt 06 should remain:

```text
RESEARCH_CANDIDATE
```

and only through the existing research gate.

No:

```text
LIVE
```

state may be introduced.

---

# 99. AI INTEGRATION

Do not build an autonomous AI trader in Prompt 06.

Prepare interfaces for future AI research agents.

Future AI may:

```text
generate hypothesis
construct feature expression
request experiment
compare feature results
summarize findings
suggest follow-up research
```

AI must not:

```text
bypass PIT
rewrite historical experiments
override integrity
promote directly to live
request live orders
```

---

# 100. AI-GENERATED FEATURE TRACEABILITY

If an AI later proposes a feature, record:

```text
proposal_id
agent/model identifier
prompt/context identifier where appropriate
timestamp
feature definition
parent hypothesis
experiment
result
```

The goal is to prevent:

```text
AI-generated research
```

from becoming an untraceable black box.

---

# 101. NO "MAGIC ALPHA"

Forbidden design:

```python
predict_stock()
```

or:

```python
ai_alpha()
```

with unexplained internals.

Every alpha must have:

```text
inputs
mathematical definition
temporal semantics
parameters
lineage
validation
```

---

# 102. RESEARCH FAMILY

Group related experiments.

Example:

```text
FAMILY: MOMENTUM

momentum_5
momentum_10
momentum_20
momentum_60
momentum_120
momentum_252
```

Then record:

```text
family size
number tested
selection process
```

This feeds Prompt 05 multiple-testing diagnostics.

---

# 103. PARAMETER SWEEP

Provide a controlled parameter-sweep framework.

Example:

```text
momentum window:
5
10
20
40
60
120
252
```

Every member must become a distinct experiment or versioned result.

Do not silently choose the best parameter.

---

# 104. PARAMETER HEATMAP DATA

Produce machine-readable surfaces:

```text
parameter
IC
OOS IC
turnover
cost-adjusted return
```

The purpose is to identify:

```text
stable regions
```

rather than:

```text
single maximum
```

---

# 105. ALPHA DECAY

A candidate alpha should eventually be analyzed for:

```text
signal decay
performance decay
IC decay
```

These are distinct concepts.

---

# 106. CAPACITY PREPARATION

Prepare metadata for future capacity analysis:

```text
ADV
participation rate
estimated market impact
position size
```

If unavailable:

```text
NOT_TESTED
```

---

# 107. FEATURE LIBRARY GOVERNANCE

Do not allow uncontrolled feature proliferation.

Every feature should have:

```text
owner/research source
definition
version
status
lineage
tests
```

Rejected features remain searchable.

---

# 108. DOCUMENTATION

Create/update documentation, avoiding duplicates.

Potential documents:

```text
docs/architecture/FEATURE_ALPHA_ENGINE.md
docs/architecture/FEATURE_SCHEMA.md
docs/architecture/LABEL_ENGINE.md
docs/architecture/ALPHA_RESEARCH.md
docs/architecture/FEATURE_LINEAGE.md
docs/research/FEATURE_RESEARCH_PROTOCOL.md
docs/research/ALPHA_RESEARCH_PROTOCOL.md
```

Use existing documentation structure if it already provides equivalent documents.

---

# 109. ADRs

Create ADRs only for genuine architectural decisions.

Do not duplicate existing ADR numbers.

Potential decisions:

```text
Feature identity/versioning
Feature expression model
Feature caching
Feature/label separation
Alpha promotion interface
```

Inspect existing ADR numbering first.

---

# 110. API BOUNDARIES

Keep:

```text
quantlab.data
quantlab.features
quantlab.labels
quantlab.alpha
quantlab.research
quantlab.validation
quantlab.backtest
quantlab.risk
quantlab.execution
quantlab.app
quantlab.ui
```

or equivalent existing namespaces.

Do not introduce circular dependencies.

Recommended dependency direction:

```text
data
 ↓
features / labels
 ↓
alpha
 ↓
research
 ↓
validation / backtest
 ↓
app
 ↓
ui
```

Lower layers must not import the UI.

---

# 111. TESTING STANDARD

Prompt 06 must add meaningful tests, not superficial coverage.

Test:

```text
feature formulas
label formulas
PIT semantics
timestamp alignment
normalization
missing values
winsorization
cross-sectional ranking
IC
quantiles
decay
correlation
lineage
versioning
caching
synthetic known-alpha
synthetic null-alpha
leakage detection
multiple-testing metadata
research gate integration
CLI
desktop service boundaries
```

---

# 112. PROPERTY-BASED TESTING

Where appropriate, test properties such as:

```text
rank output preserves ordering
z-score has approximately zero mean when defined
constant feature has undefined/zero variance behavior explicitly handled
future data cannot affect historical feature values
changing feature version changes identity
```

---

# 113. REPRODUCIBILITY

A feature experiment must be reproducible from:

```text
dataset snapshot
feature version
label version
universe
configuration
code version
seed where applicable
```

---

# 114. EXPERIMENT LEDGER

Append to the existing ledger.

Record at minimum:

```text
experiment_id
hypothesis_id
feature_id
feature_version
alpha_id
dataset_id
snapshot_id
configuration_hash
research_family_id
timestamp
result
status
integrity
validation_summary
```

Do not create a second ledger.

---

# 115. RESEARCH RESULT LANGUAGE

Use disciplined status language.

Prefer:

```text
positive association
negative association
weak evidence
statistically uncertain
robust across tested windows
fragile
insufficient data
not tested
```

Avoid:

```text
guaranteed alpha
sure winner
profitable stock
AI knows
```

---

# 116. PERFORMANCE REPORTING

A feature research report should eventually resemble:

```text
QUANT LAB FEATURE RESEARCH REPORT
==================================

Feature:
Version:
Hypothesis:
Dataset:
Snapshot:
Universe:

MATHEMATICAL DEFINITION
-----------------------
...

DATA QUALITY
------------
Coverage:
Missingness:
Variance:
PIT Integrity:

PREDICTIVE POWER
----------------
Horizon:
Mean IC:
Median IC:
IC Std:
IC Hit Rate:
Statistical Evidence:

QUANTILE ANALYSIS
-----------------
Q1:
Q2:
Q3:
Q4:
Q5:
Spread:
Monotonicity:

DECAY
-----
1D:
5D:
10D:
20D:
60D:

REDUNDANCY
----------
Correlated Features:

ROBUSTNESS
----------
Regime:
Period:
Universe:
Parameter:

ECONOMIC VALIDATION
-------------------
Turnover:
Costs:
Slippage:
OOS:

MULTIPLE TESTING
----------------
Family:
Trials:
Correction:

RESEARCH GATE
-------------
Status:
Warnings:
Reasons:
```

---

# 117. ACCEPTANCE CRITERIA

Prompt 06 is complete only when:

```text
✓ Prompts 01–05 remain intact.
✓ No second data fabric is created.
✓ No second backtester is created.
✓ No second validation engine is created.
✓ Feature becomes a first-class versioned research object.
✓ Mathematical feature definitions exist.
✓ PIT semantics are enforced.
✓ Feature/label separation exists.
✓ Forward-label engine exists.
✓ Initial primitive feature library exists.
✓ Cross-sectional transformations exist.
✓ Time-series transformations exist.
✓ Normalization is explicit.
✓ Missing-value policy is explicit.
✓ Feature quality diagnostics exist.
✓ Feature distribution stability can be analyzed.
✓ Feature correlation/redundancy analysis exists.
✓ Pearson IC exists where appropriate.
✓ Spearman Rank IC exists where appropriate.
✓ Quantile analysis exists.
✓ Quantile monotonicity diagnostics exist.
✓ Signal/IC decay exists.
✓ Alpha abstraction exists.
✓ Feature-to-alpha bridge exists.
✓ Transparent alpha combinations exist.
✓ Hypothesis registry integration exists.
✓ Multiple-testing metadata integrates with Prompt 05.
✓ Parameter sweeps are traceable.
✓ Feature lineage exists.
✓ Computation dependencies are traceable.
✓ Feature caching is reproducible.
✓ Synthetic known-signal tests exist.
✓ Synthetic null-signal tests exist.
✓ Synthetic leakage tests exist.
✓ Historical experiments cannot be silently deleted.
✓ Experiment ledger integration exists.
✓ Research gate remains authoritative.
✓ Synthetic results cannot become research candidates.
✓ AI cannot bypass research controls.
✓ LIVE_TRADING remains false.
✓ Desktop uses application services.
✓ UI does not access raw data directly.
✓ CLI integration exists.
✓ Documentation is updated.
✓ ADRs are created only where necessary.
✓ Tests are expanded meaningfully.
✓ ruff is clean.
✓ mypy --strict is clean.
✓ Existing full test suite passes.
✓ Existing `quantlab slice` remains functional.
✓ Existing backtest commands remain functional.
✓ Existing validation commands remain functional.
```

---

# 118. CRITICAL INVARIANTS

## INVARIANT 1 — PIT

```text
feature.available_time <= decision_time
```

## INVARIANT 2 — LABEL

```text
label uses future information only as a label
```

and never enters feature computation.

## INVARIANT 3 — UNIVERSE

```text
Universe(T)
```

must be historical/as-of correct.

## INVARIANT 4 — VERSIONING

Changing a mathematical definition creates a new version.

## INVARIANT 5 — LINEAGE

Every feature result is traceable to its inputs and snapshot.

## INVARIANT 6 — MULTIPLE TESTING

Repeated experimentation remains visible.

## INVARIANT 7 — REPRODUCIBILITY

Same inputs and configuration produce reproducible results.

## INVARIANT 8 — UNKNOWN

```text
NOT_TESTED ≠ PASS
```

## INVARIANT 9 — SYNTHETIC

```text
synthetic evidence ≠ market evidence
```

## INVARIANT 10 — AI

AI cannot override research integrity.

## INVARIANT 11 — LIVE

Live trading remains disabled.

---

# 119. WHAT NOT TO BUILD IN PROMPT 06

Do NOT implement:

```text
live trading
Zerodha execution
OpenAlgo live execution
autonomous trading agent
reinforcement-learning trader
LLM stock picker
black-box "AI alpha"
deep-learning model zoo
HFT execution engine
distributed cluster
```

Those belong to later phases.

Prompt 06 is about building the **scientific alpha-discovery substrate**.

---

# 120. DEFINITION OF DONE

The laboratory should now be able to execute:

```text
Research Hypothesis
       ↓
Feature Definition
       ↓
PIT Feature Computation
       ↓
Forward Label
       ↓
Cross-Sectional / Time-Series Analysis
       ↓
IC
       ↓
Quantile Analysis
       ↓
Decay
       ↓
Feature Redundancy
       ↓
Alpha Transformation
       ↓
Prompt 05 OOS Validation
       ↓
Robustness
       ↓
Statistical Evaluation
       ↓
Multiple-Test Awareness
       ↓
Research Gate
       ↓
Experiment Ledger
```

The system must be able to answer:

```text
What was the feature?

What information did it use?

When was that information available?

What universe was used?

What was the mathematical definition?

What future outcome was tested?

At what horizons?

How strong was the relationship?

Did the relationship persist across time?

Did it survive different parameters?

Did it survive different regimes?

Was it redundant with known features?

How many related hypotheses were tested?

Did it survive out-of-sample validation?

Did transaction costs destroy it?

What does the integrity engine say?

Why was it accepted or rejected?
```

---

# 121. FINAL ENGINEERING DIRECTIVE

Do not build an "indicator dashboard."

Build a **quantitative hypothesis-testing laboratory**.

The fundamental unit of QUANT LAB research should become:

```text
HYPOTHESIS
     ↓
MEASUREMENT
     ↓
FEATURE
     ↓
PREDICTION
     ↓
STATISTICAL EVIDENCE
     ↓
ECONOMIC EVIDENCE
     ↓
ROBUSTNESS
     ↓
REPRODUCIBLE CONCLUSION
```

The objective is not to discover the most complicated feature.

The objective is to discover whether a simple measurable relationship contains **persistent, statistically defensible, economically meaningful predictive information**.

Every result must be reproducible.

Every experiment must be traceable.

Every unknown must remain unknown.

Every failure is valid research.

Every apparent alpha must earn the right to survive the next experiment.

**Implement Prompt 06 on top of the existing QUANT LAB 0.5 architecture.**
