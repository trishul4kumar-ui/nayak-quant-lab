# QUANT LAB — CURSOR MASTER PROMPT 05
# RESEARCH-GRADE BACKTESTING & VALIDATION ENGINE

**Version:** 0.5  
**Date:** 2026-08-30  
**Project:** QUANT LAB  
**Mission:** Turn the existing PIT-correct research core into a statistically rigorous quantitative research laboratory.

---

# 0. EXECUTION DIRECTIVE

You are continuing the existing QUANT LAB repository.

## NON-NEGOTIABLE

**DO NOT RESET THE REPOSITORY.**

**DO NOT REWRITE THE EXISTING QUANTITATIVE CORE.**

**DO NOT REMOVE OR BYPASS PROMPTS 01–04.**

Preserve all existing architecture and functionality:

- Prompt 01 — repository study / architecture foundation
- Prompt 02 — quantitative core and safety architecture
- Prompt 03 — native desktop application
- Prompt 04 — Point-in-Time Data Fabric

Current guarantees that MUST remain intact:

```text
next-bar fills
10 bps default transaction costs
LIVE_TRADING=false
live execution fail-closed
AI cannot request live orders
strategies cannot import brokers
desktop is a client of quantlab.app
PIT available_time <= as_of
dataset provenance
dataset versioning
research integrity
experiment ledger
lineage
synthetic/real data separation
```

Current baseline:

```text
70+ tests
ruff clean
mypy --strict clean
```

The exact current test count must be discovered from the repository rather than assumed.

---

# 1. PURPOSE

The objective of Prompt 05 is to build a:

> **Research-Grade Backtesting & Validation Engine**

The engine must answer a substantially harder question than:

> "Did this strategy make money?"

It must answer:

> **"Does this observed strategy effect survive realistic execution assumptions, temporal validation, out-of-sample testing, parameter perturbation, market-regime changes, statistical testing, and multiple-hypothesis correction?"**

The system must therefore distinguish:

```text
BACKTEST PERFORMANCE
        ≠
ROBUST ALPHA
```

and:

```text
HIGH SHARPE
        ≠
STATISTICAL SIGNIFICANCE
```

and:

```text
OUT-OF-SAMPLE
        ≠
AUTOMATICALLY VALID
```

---

# 2. SCIENTIFIC PHILOSOPHY

QUANT LAB is intended to become a mathematical/statistical research laboratory inspired by systematic quantitative research.

Do NOT optimize for:

```text
highest Sharpe
highest CAGR
best-looking equity curve
largest number of strategies
```

Optimize for:

```text
falsifiability
reproducibility
statistical discipline
temporal correctness
economic significance
robustness
research traceability
```

A strategy that fails rigorous validation is a successful research outcome.

---

# 3. CURRENT DATA FLOW

Preserve:

```text
Source
 ↓
Immutable Raw
 ↓
Checksum
 ↓
Normalization
 ↓
Validation
 ↓
Parquet
 ↓
DuckDB
 ↓
Point-in-Time Query
 ↓
MarketState
 ↓
Feature
 ↓
Signal
 ↓
Portfolio
 ↓
Risk Firewall
 ↓
Next-Bar Backtest
 ↓
Research Integrity
 ↓
Experiment Ledger
```

Prompt 05 inserts a rigorous validation layer around the backtesting process:

```text
PIT Data
   ↓
Research Configuration
   ↓
Backtest
   ↓
Performance Analytics
   ↓
Walk-Forward Validation
   ↓
Out-of-Sample Evaluation
   ↓
Robustness Tests
   ↓
Statistical Tests
   ↓
Multiple-Testing Diagnostics
   ↓
Research Integrity
   ↓
Promotion / Rejection Gate
   ↓
Experiment Ledger
```

---

# 4. DO NOT BREAK THE EXISTING BACKTESTER

First inspect the existing backtesting implementation.

Identify:

```text
backtest modules
portfolio accounting
fill model
cost model
risk firewall
MarketState
PIT provider
integrity engine
experiment ledger
lineage
CLI
desktop integration
tests
```

Extend existing abstractions where possible.

Do not create a competing backtester.

---

# 5. BACKTEST CONTRACT

Define a typed, reproducible backtest configuration.

Conceptually:

```python
BacktestConfig(
    dataset_id=...,
    dataset_version=...,
    snapshot_id=...,
    start=...,
    end=...,
    universe=...,
    strategy_version=...,
    feature_versions=...,
    initial_capital=...,
    costs=...,
    slippage=...,
    fill_policy=...,
    rebalance_frequency=...,
    position_limits=...,
)
```

The exact API is an engineering decision.

Every backtest must have a deterministic configuration identity/hash.

---

# 6. BACKTEST RESULT CONTRACT

A backtest result must contain more than P&L.

Include conceptually:

```text
experiment_id
backtest_id
dataset identity
configuration identity
period
universe
strategy version
feature versions
initial capital
ending capital
returns
equity curve
drawdown
turnover
transaction costs
slippage
exposure
positions
trades
risk events
integrity report
```

---

# 7. PERFORMANCE METRICS

Build a typed performance analytics layer.

At minimum support:

## Return

```text
cumulative return
CAGR
periodic returns
```

## Risk

```text
volatility
maximum drawdown
average drawdown
drawdown duration
```

## Risk-adjusted

```text
Sharpe ratio
Sortino ratio
Calmar ratio
```

## Trading

```text
turnover
trade count
hit rate
average win
average loss
profit factor
average holding period
```

## Exposure

```text
gross exposure
net exposure
cash
leverage
```

## Distribution

```text
skewness
kurtosis
tail losses
```

Do not silently assume a risk-free rate.

Make the risk-free-rate convention explicit.

---

# 8. RETURN DEFINITIONS

Document precisely:

```text
simple return
log return
portfolio return
asset return
```

Do not mix them without explicit conversion.

---

# 9. ANNUALIZATION

Centralize annualization conventions.

Do not scatter:

```python
sqrt(252)
```

through the codebase.

Create a market-calendar-aware convention.

For Indian equities, trading-session assumptions must come from the calendar abstraction rather than hardcoded magic numbers where possible.

---

# 10. DRAWDOWN ENGINE

Implement:

```text
peak equity
current equity
drawdown
maximum drawdown
drawdown start
drawdown trough
recovery
recovery duration
```

Support analysis of:

```text
top drawdowns
```

not merely the maximum.

---

# 11. BENCHMARKING

Design a benchmark abstraction.

Support future benchmarks such as:

```text
NIFTY 50
NIFTY 500
BSE Sensex
custom benchmark
cash/risk-free benchmark
```

Do not fabricate benchmark history.

If benchmark data is unavailable:

```text
NOT_TESTED
```

---

# 12. FACTOR / BENCHMARK ATTRIBUTION

Create an architecture for determining whether returns are simply explained by common exposures.

Support future analysis such as:

```text
market beta
size
value
momentum
volatility
quality
sector exposure
```

Do not claim alpha merely because portfolio return is positive.

---

# 13. WALK-FORWARD VALIDATION

This is a CORE requirement.

Implement rolling and expanding walk-forward validation.

Example:

```text
TRAIN              TEST
2015 ── 2018  →    2019
2016 ── 2019  →    2020
2017 ── 2020  →    2021
2018 ── 2021  →    2022
2019 ── 2022  →    2023
2020 ── 2023  →    2024
2021 ── 2024  →    2025
```

Support:

```text
rolling window
expanding window
anchored window
```

The exact windows must be configurable.

---

# 14. TRAIN / VALIDATION / TEST

Define explicit dataset roles:

```text
TRAIN
VALIDATION
TEST
```

No test-period optimization.

The test set is sacred.

If configuration was selected using test results, mark the experiment as contaminated.

---

# 15. PURGED TIME-SERIES VALIDATION

Prepare the validation engine for overlapping labels.

Implement a purge mechanism when label horizons overlap training and validation observations.

Example:

```text
training observation
label horizon ────────────┐
                           │ overlap
validation observation ────┘
```

The overlapping training observation must be removed where required.

---

# 16. EMBARGO

Implement configurable embargo periods after training samples before validation/test observations.

Conceptually:

```text
TRAIN
████████████████

EMBARGO
        ░░░░░░

TEST
             ████████
```

The embargo must be measured using the appropriate temporal convention.

---

# 17. LABEL HORIZON AWARENESS

Validation must understand that future labels can extend beyond the nominal observation timestamp.

Example:

```text
feature_time = T
label horizon = T → T+20
```

The validation engine must not treat this as a point observation with no future dependency.

---

# 18. LOOK-AHEAD DETECTION

Expand the existing integrity system.

Detect:

```text
future feature
future label
future universe
future corporate action
future fundamental revision
future benchmark
future normalization
future parameter selection
```

Research integrity should produce:

```text
PASS
WARN
FAIL
NOT_TESTED
```

---

# 19. COST MODEL

The existing default:

```text
10 bps
```

must remain.

But Prompt 05 should build a configurable cost framework.

Support:

```text
commission
exchange fees
taxes
slippage
bid/ask spread
market impact
stamp duty
STT
GST
SEBI/other applicable charges
```

Do not invent exact Indian fee schedules.

Use configuration/data sources when available.

---

# 20. COST SENSITIVITY

Every serious strategy evaluation should support multiple cost assumptions.

Example:

```text
0 bps
5 bps
10 bps
20 bps
50 bps
100 bps
```

But note:

> A zero-cost backtest is not evidence of tradability.

Keep the existing rule that the default research configuration contains non-zero costs.

---

# 21. SLIPPAGE MODEL

Build a pluggable slippage model.

Minimum architecture:

```text
NoSlippage
FixedBpsSlippage
SpreadSlippage
VolumeParticipationSlippage
```

Do not pretend these models are equally realistic.

Record the selected model in the experiment.

---

# 22. MARKET IMPACT

Create an interface for future market-impact models.

Conceptually:

```text
impact ∝ function(
    order_size,
    ADV,
    volatility,
    spread,
    liquidity
)
```

Do not claim a validated impact model unless supported by data.

---

# 23. TURNOVER ANALYSIS

Calculate:

```text
daily turnover
average turnover
annual turnover
turnover by instrument
turnover by rebalance
```

A high-return strategy with extreme turnover must be visibly flagged.

---

# 24. LIQUIDITY FILTERS

Prepare architecture for:

```text
ADV
volume
market cap
spread
price
participation rate
```

Strategies must not silently assume infinite liquidity.

---

# 25. POSITION LIMITS

Integrate with the existing Risk Firewall.

Test:

```text
single-name limit
sector limit
gross exposure
net exposure
cash limit
turnover limit
liquidity limit
```

Do not duplicate risk logic.

---

# 26. REGIME ANALYSIS

Implement a regime-analysis framework.

Potential regimes:

```text
bull
bear
high volatility
low volatility
high correlation
low correlation
trending
mean-reverting
```

The first implementation may use configurable/simple definitions.

Do not claim regimes are objectively true.

Record the regime methodology.

---

# 27. PERFORMANCE BY REGIME

For each regime calculate:

```text
return
Sharpe
drawdown
volatility
turnover
exposure
```

This allows detection of:

```text
strategy works only in one market regime
```

---

# 28. PARAMETER SENSITIVITY

A robust strategy should not depend on one magic parameter.

Example:

```text
momentum window:
10
15
20
25
30
40
60
```

Generate parameter surfaces.

Evaluate:

```text
performance stability
```

rather than merely choosing:

```text
maximum Sharpe
```

---

# 29. PARAMETER FRAGILITY

Flag cases where:

```text
parameter = 20 → excellent
parameter = 19 → poor
parameter = 21 → poor
```

This is a potential overfitting warning.

Prefer broad plateaus:

```text
18–25 → similar behavior
```

---

# 30. BOOTSTRAP TESTING

Implement a statistical bootstrap framework where appropriate.

Possible methods:

```text
IID bootstrap
block bootstrap
stationary bootstrap
```

Time-series dependence must be respected.

Do not randomly shuffle financial returns blindly and call it a valid statistical test.

---

# 31. PERMUTATION / NULL TESTING

Create a framework for null-hypothesis testing.

Examples:

```text
signal permutation
label permutation
time-block permutation
```

The null model must be explicit.

The result should answer:

> How often could an effect of this magnitude arise under the specified null?

---

# 32. STATISTICAL SIGNIFICANCE

Do not rely solely on:

```text
p < 0.05
```

Support reporting of:

```text
effect size
confidence interval
sample size
standard error
p-value
null model
```

Statistical significance and economic significance must be separately reported.

---

# 33. AUTOCORRELATION

Return and signal statistics must account for temporal dependence where relevant.

Do not assume observations are IID without justification.

---

# 34. HETEROSKEDASTICITY

Where regression/statistical inference is introduced, prepare support for heteroskedasticity-robust inference.

Do not implement statistical tests with hidden assumptions.

---

# 35. MULTIPLE TESTING — CRITICAL

This is one of the most important Prompt 05 requirements.

QUANT LAB will eventually test:

```text
features
parameters
universes
holding periods
models
cost assumptions
regimes
```

Therefore the system must track:

```text
number of hypotheses tested
hypothesis family
experiment lineage
selection process
```

---

# 36. RESEARCH MULTIPLE-TEST LEDGER

Add metadata such as:

```text
research_family_id
hypothesis_id
experiment_id
parent_experiment_id
number_of_tests
selection_stage
```

A strategy discovered after 100,000 trials must not be treated as equivalent to a pre-registered hypothesis tested once.

---

# 37. FALSE DISCOVERY RATE

Prepare support for methods such as:

```text
Benjamini-Hochberg
```

where appropriate.

Make the statistical method explicit.

---

# 38. FAMILY-WISE ERROR

Prepare support for methods such as:

```text
Bonferroni
Holm
```

where appropriate.

Do not automatically apply one method to every research problem.

---

# 39. DEFLATED SHARPE RATIO

Implement an architecture for correcting naive Sharpe interpretation when many trials and non-normality are involved.

The report should clearly distinguish:

```text
naive Sharpe
```

from:

```text
multiple-testing-aware interpretation
```

Do not manufacture a correction if required inputs are unavailable.

---

# 40. PROBABILITY OF BACKTEST OVERFITTING

Create an extensible diagnostic framework for:

```text
PBO
```

or equivalent overfitting diagnostics.

The implementation must document assumptions and limitations.

---

# 41. BACKTEST OVERFITTING REPORT

Produce a structured report:

```text
Research Overfitting Report
---------------------------
Experiments tested:
Parameter combinations:
Selection mechanism:
Out-of-sample windows:
Multiple-testing adjustment:
Sharpe stability:
Parameter stability:
Cost stability:
Regime stability:
Statistical evidence:
Warnings:
```

---

# 42. DATA-SNOOPING PROTECTION

The experiment system must make research history visible.

If a researcher repeatedly modifies:

```text
feature
parameter
universe
holding period
cost model
```

after observing test results, the ledger should preserve that lineage.

Do not allow deletion/rewrite of historical experiment records through normal research APIs.

---

# 43. HYPOTHESIS REGISTRY

Prepare an explicit hypothesis object.

Conceptually:

```text
Hypothesis
├── hypothesis_id
├── statement
├── rationale
├── expected_direction
├── target
├── feature_set
├── universe
├── horizon
├── pre_registered_parameters
└── status
```

Statuses may include:

```text
PROPOSED
TESTING
SUPPORTED
REJECTED
CONTAMINATED
DEPRECATED
```

Do not force every experiment to be pre-registered yet, but build the architecture for it.

---

# 44. RESEARCH PROMOTION GATE

Create a configurable research gate.

Example:

```text
                RESEARCH GATE
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
   Integrity      Statistical     Robustness
       │              │              │
       └──────────────┼──────────────┘
                      ▼
                OUT-OF-SAMPLE
                      │
                      ▼
                 PROMOTION
```

Possible outcomes:

```text
REJECT
WARN
RESEARCH_CANDIDATE
PROMOTED_TO_PAPER
```

Do NOT create a live-trading promotion state in Prompt 05.

---

# 45. PROMOTION CRITERIA

The gate must be configurable.

Possible checks:

```text
PIT integrity
no critical leakage
out-of-sample evidence
cost robustness
parameter robustness
regime robustness
statistical evidence
liquidity feasibility
drawdown constraints
risk compliance
```

No single metric should automatically promote a strategy.

---

# 46. BENCHMARK COMPARISON

When benchmark data exists, report:

```text
strategy return
benchmark return
excess return
tracking error
information ratio
beta
alpha
```

If benchmark data does not exist:

```text
NOT_TESTED
```

---

# 47. FACTOR NEUTRALITY / EXPOSURE

Prepare analysis for:

```text
market beta
sector concentration
momentum exposure
size exposure
value exposure
volatility exposure
```

A future alpha may simply rediscover momentum.

The laboratory should help expose this.

---

# 48. SUBPERIOD STABILITY

Every validation report should support performance by:

```text
year
quarter
month
custom period
```

This helps identify:

```text
single-period dependence
```

---

# 49. CROSS-SECTIONAL ANALYSIS

Prepare support for cross-sectional research metrics:

```text
rank IC
Pearson IC
Spearman IC
IC mean
IC standard deviation
IC information ratio
IC decay
```

This is important for the future Alpha Research Engine.

Do not require all metrics for the current momentum strategy if the data contract is not yet ready.

---

# 50. SIGNAL DECAY

Prepare a signal-decay analysis:

```text
signal at T
 ↓
return T+1
return T+2
return T+3
...
return T+n
```

This becomes important for determining:

```text
holding period
```

and:

```text
execution urgency
```

---

# 51. PORTFOLIO CONSTRUCTION VALIDATION

Evaluate strategy behavior under different portfolio rules where applicable:

```text
top-N
equal weight
volatility weight
risk weight
signal weight
```

Do not optimize all choices against the final test set.

Track each configuration as an experiment.

---

# 52. RANDOM BASELINES

Provide baseline strategies where appropriate:

```text
equal-weight market
random signal
random portfolio
buy-and-hold benchmark
```

Random baselines must be deterministic when used in tests.

Use seeds and record them.

---

# 53. REPRODUCIBILITY

Every validation run must record:

```text
random seed
software version
dataset version
snapshot checksum
strategy version
feature versions
configuration hash
validation protocol
```

Two identical experiments should be reproducible to the extent permitted by the algorithms.

---

# 54. DETERMINISTIC EXECUTION

Avoid hidden nondeterminism.

If stochastic algorithms are introduced:

```text
seed them
record seeds
record algorithm version
```

---

# 55. EXPERIMENT COMPARISON

Create a structured comparison layer.

Example:

```text
Experiment A
Experiment B
Experiment C
```

Compare:

```text
OOS return
Sharpe
drawdown
turnover
cost sensitivity
parameter sensitivity
regime stability
statistical evidence
```

Never rank strategies using one metric alone.

---

# 56. EXPERIMENT LINEAGE

Maintain:

```text
Parent hypothesis
      ↓
Experiment A
      ↓
Experiment B
      ↓
Experiment C
```

If B is a modification of A, the lineage must show that.

This is essential for detecting researcher selection bias.

---

# 57. RESEARCH ARTIFACTS

A completed validation should produce machine-readable artifacts.

For example:

```text
results/
    experiment_id/
        config.json
        metrics.json
        equity.parquet
        trades.parquet
        validation.json
        integrity.json
        lineage.json
```

Do not hardcode this exact filesystem structure if the repository already has a better artifact architecture.

---

# 58. JSON SCHEMAS

Where appropriate, define versioned schemas for:

```text
BacktestResult
PerformanceReport
ValidationReport
RobustnessReport
StatisticalReport
ResearchGateResult
```

Schema evolution must be explicit.

---

# 59. CLI

Extend the existing CLI.

Conceptual commands:

```text
quantlab backtest run <config>
quantlab backtest report <experiment>
quantlab validate run <experiment>
quantlab validate walk-forward <experiment>
quantlab validate robustness <experiment>
quantlab validate statistics <experiment>
quantlab research compare <experiment-a> <experiment-b>
quantlab research gate <experiment>
```

Do not create a second CLI framework.

---

# 60. DESKTOP INTEGRATION

The desktop should remain a presentation/client layer.

Add appropriate Research/Validation views only after the application services exist.

Possible views:

```text
Backtest
Validation
Robustness
Statistics
Research Gate
Experiment Comparison
```

The UI must NOT:

```text
calculate statistics independently
read Parquet directly
bypass application services
change research results
```

---

# 61. PERFORMANCE

The validation engine should support large experiments.

Use:

```text
vectorized operations where appropriate
Parquet
DuckDB
streaming/chunking
parallelism where deterministic and safe
```

Do not prematurely distribute computation.

Correctness first.

---

# 62. CACHING

Cache expensive deterministic calculations where appropriate.

Cache keys must include all inputs that affect results.

Example:

```text
dataset snapshot
strategy version
feature version
configuration hash
```

A cache hit must never return results from a different research configuration.

---

# 63. FAILURE-CLOSED VALIDATION

If a validation prerequisite is missing:

```text
NOT_TESTED
```

or:

```text
FAIL
```

Do not substitute:

```text
WARN → PASS
```

Do not fabricate missing statistical evidence.

---

# 64. CURRENT SYNTHETIC DATA

The existing synthetic dataset may continue to be used for deterministic architecture tests.

But:

```text
synthetic performance ≠ market evidence
```

The validation report must identify:

```text
data_kind=synthetic
```

and clearly prevent promotion to paper/live research solely from synthetic results.

---

# 65. REAL DATA

When real Indian-market data is available through Prompt 04:

```text
PIT Data Fabric
 ↓
Backtest
 ↓
Validation
```

must use the same engine.

No special "real data" backtester.

---

# 66. INDIAN MARKET AWARENESS

Prepare architecture for:

```text
NSE
BSE
IST
Indian trading sessions
corporate actions
Indian transaction costs
market holidays
```

Do not hardcode unofficial assumptions into generic statistics.

---

# 67. STATISTICAL REPORT FORMAT

A validation report should eventually resemble:

```text
QUANT LAB RESEARCH VALIDATION REPORT
====================================

Experiment:
Dataset:
Snapshot:
Strategy:
Universe:
Period:

PERFORMANCE
-----------
CAGR:
Volatility:
Sharpe:
Sortino:
Calmar:
Max Drawdown:
Turnover:

OUT-OF-SAMPLE
-------------
Windows:
OOS Return:
OOS Sharpe:
OOS Drawdown:

ROBUSTNESS
----------
Cost:
Slippage:
Parameters:
Regimes:
Liquidity:

STATISTICS
----------
Sample Size:
Effect Size:
Confidence Interval:
P-Value:
Null Model:

MULTIPLE TESTING
----------------
Hypotheses Tested:
Correction:
Adjusted Evidence:

INTEGRITY
---------
PIT:
Look-Ahead:
Survivorship:
Corporate Actions:
Costs:
Data Quality:

RESEARCH GATE
-------------
Result:
Reasons:
Warnings:
```

---

# 68. RESEARCH SCORE — USE CAUTION

If implementing an aggregate research score, it must NOT be:

```text
Sharpe × arbitrary weights
```

Prefer a transparent rule-based gate.

The system must expose the individual reasons behind a decision.

---

# 69. NO BLACK-BOX PROMOTION

Prohibited:

```text
AI says strategy is good
        ↓
PROMOTE
```

Required:

```text
Integrity
+
OOS evidence
+
Robustness
+
Statistics
+
Research history
        ↓
Human-readable gate
```

AI can eventually assist interpretation, but cannot override the gate.

---

# 70. MULTIPLE-EXPERIMENT MEMORY

The experiment ledger must become the laboratory's memory.

The system should eventually answer:

```text
How many momentum hypotheses have we tested?
Which parameters have been explored?
Which datasets were used?
Which experiments were rejected?
Why were they rejected?
Which ideas were selected after observing test results?
```

This is critical for avoiding repeated rediscovery and hidden data mining.

---

# 71. TEST SUITE

Add rigorous tests.

## Backtest

```text
next-bar fill
cost application
cash accounting
position accounting
```

## Metrics

```text
return
CAGR
Sharpe
Sortino
drawdown
turnover
```

## Walk-forward

```text
window generation
train/test separation
expanding windows
rolling windows
```

## Purging

```text
overlapping labels removed
```

## Embargo

```text
embargo enforced
```

## Costs

```text
cost sensitivity
slippage
```

## Statistics

```text
bootstrap
permutation
confidence intervals
```

## Multiple Testing

```text
hypothesis counting
FDR/FWER
selection lineage
```

## Integrity

```text
PIT
look-ahead
survivorship status
```

## Reproducibility

```text
same seed
same configuration
same dataset snapshot
```

---

# 72. PROPERTY TESTS

Where appropriate, test mathematical properties.

Examples:

```text
max_drawdown <= 0
```

```text
ending_equity >= 0
```

```text
transaction_costs >= 0
```

```text
OOS timestamps never overlap forbidden training information
```

```text
PIT query never returns unavailable information
```

```text
validation windows are temporally ordered
```

---

# 73. EDGE CASES

Explicitly test:

```text
no trades
one trade
zero return
constant return
negative return
missing bars
missing feature
empty universe
single instrument
delisted instrument
partial period
large drawdown
all positions rejected by risk
zero cash
```

No NaN/Infinity should silently enter final reports.

---

# 74. NUMERICAL STABILITY

Use stable numerical methods.

Guard against:

```text
division by zero
zero volatility
empty samples
floating-point instability
overflow
NaN
Infinity
```

Reports must distinguish:

```text
undefined
zero
not tested
```

These are not equivalent.

---

# 75. DOCUMENTATION

Create/update documentation such as:

```text
docs/architecture/RESEARCH_VALIDATION_ENGINE.md
docs/architecture/WALK_FORWARD_VALIDATION.md
docs/architecture/STATISTICAL_VALIDATION.md
docs/architecture/MULTIPLE_TESTING.md
docs/architecture/RESEARCH_GATES.md
docs/development/BACKTESTING_PROTOCOL.md
```

Inspect existing docs before creating duplicates.

Create ADRs only where a real architectural decision is being made.

Do not duplicate existing ADR numbers.

---

# 76. RESEARCH PROTOCOL

Document a canonical research workflow:

```text
1. Define hypothesis
2. Select permitted dataset
3. Freeze PIT snapshot
4. Define universe
5. Define feature
6. Define strategy
7. Define validation protocol
8. Run training
9. Run validation
10. Run untouched test
11. Run robustness tests
12. Run statistical tests
13. Evaluate multiple-testing exposure
14. Run research gate
15. Record result
```

---

# 77. TEST-SET PROTECTION

The system should make it difficult to accidentally use test results during optimization.

At minimum:

```text
test data is explicitly labelled
test evaluation produces immutable experiment evidence
```

Design for future stronger controls.

---

# 78. STRATEGY VERSIONING

A strategy change must create a new version.

Example:

```text
momentum_20:v1
momentum_20:v2
```

Do not overwrite the definition used by previous experiments.

---

# 79. FEATURE VERSIONING

Same requirement for features.

Example:

```text
momentum_20:v1
momentum_20:v2
```

A changed formula is a new feature version.

---

# 80. CONFIGURATION VERSIONING

Changes to:

```text
cost
slippage
rebalance
portfolio construction
risk
validation
```

must be visible in experiment lineage.

---

# 81. RESEARCH ENVIRONMENT

Record relevant environment information:

```text
Python version
package versions
Git commit
OS
configuration hash
```

Do not require exact machine identity if it creates unnecessary privacy or portability issues.

---

# 82. GIT STATE

Where possible, record:

```text
Git commit SHA
dirty/clean state
```

A research result generated from an uncommitted workspace should be visibly marked.

---

# 83. SECURITY / SAFETY

Prompt 05 must not introduce:

```text
live trading
broker orders
automatic capital deployment
```

The existing safety architecture remains authoritative.

---

# 84. AI INTERFACE

Prepare interfaces for future AI research agents.

AI may eventually:

```text
propose hypothesis
request experiment
compare results
interpret diagnostics
```

AI must NOT:

```text
bypass PIT
change immutable experiment records
override research gate
place live orders
```

---

# 85. NO ML IMPLEMENTATION YET

Do NOT turn Prompt 05 into a machine-learning implementation.

The goal is to make the research environment rigorous enough that future ML experiments cannot hide methodological weaknesses.

ML comes after the validation foundation is reliable.

---

# 86. ACCEPTANCE CRITERIA

Prompt 05 is complete only when:

```text
✓ Existing Prompts 01–04 remain intact.
✓ Existing synthetic slice still works.
✓ Existing PIT semantics remain intact.
✓ Existing next-bar fill remains intact.
✓ Existing 10 bps default cost remains intact.
✓ LIVE_TRADING remains false.
✓ Backtest configuration is typed and reproducible.
✓ Performance analytics are implemented.
✓ Drawdown analytics are implemented.
✓ Walk-forward validation is implemented.
✓ Rolling/expanding windows are supported.
✓ Train/validation/test separation exists.
✓ Purging is implemented where label overlap requires it.
✓ Embargo is configurable.
✓ Slippage is pluggable.
✓ Cost sensitivity is supported.
✓ Parameter sensitivity is supported.
✓ Regime analysis framework exists.
✓ Bootstrap/statistical framework exists.
✓ Null/permutation framework exists where appropriate.
✓ Multiple-testing metadata is tracked.
✓ FDR/FWER methods are available where appropriate.
✓ Overfitting diagnostics architecture exists.
✓ Experiment lineage records research evolution.
✓ Research gate exists.
✓ Benchmark/factor attribution architecture exists.
✓ Signal decay architecture exists.
✓ Experiment comparison exists.
✓ Results are reproducible.
✓ Results are machine-readable.
✓ Research Integrity integrates with validation.
✓ NOT_TESTED remains NOT_TESTED.
✓ Synthetic results cannot be promoted as market evidence.
✓ Desktop remains a client of application services.
✓ UI cannot bypass research services.
✓ AI cannot bypass research services.
✓ No live trading is introduced.
✓ Tests are meaningfully expanded.
✓ ruff remains clean.
✓ mypy --strict remains clean.
✓ Documentation is updated.
✓ ADRs are created only for actual new architectural decisions.
```

---

# 87. CRITICAL INVARIANTS

These must never be violated.

### INVARIANT 1 — TEMPORAL

```text
available_time <= decision_time
```

for all information available to the strategy.

### INVARIANT 2 — NEXT-BAR

Signals cannot fill on the same bar that generated them.

### INVARIANT 3 — COST

Research-grade default backtests contain non-zero transaction costs.

### INVARIANT 4 — TEST

Test-period results cannot silently become training information.

### INVARIANT 5 — LINEAGE

Every experiment is traceable.

### INVARIANT 6 — MULTIPLE TESTING

Repeated experimentation must be visible.

### INVARIANT 7 — REPRODUCIBILITY

Same inputs + same configuration + same seed must produce reproducible results where algorithms permit.

### INVARIANT 8 — INTEGRITY

A failed integrity check cannot be converted into a successful research result.

### INVARIANT 9 — UNKNOWN

Unknown ≠ false.

```text
NOT_TESTED ≠ PASS
```

### INVARIANT 10 — SYNTHETIC

Synthetic performance is never market evidence.

### INVARIANT 11 — AI

AI cannot override research integrity.

### INVARIANT 12 — LIVE

Live trading remains disabled.

---

# 88. DEFINITION OF RESEARCH-GRADE

Do not claim that a strategy is "validated" merely because:

```text
Sharpe > 1
```

or:

```text
return > benchmark
```

A strategy is only a:

```text
RESEARCH CANDIDATE
```

when the configured validation protocol has been satisfied.

Even then, it is not necessarily tradable.

The final conceptual hierarchy is:

```text
BACKTESTED
    ↓
OUT-OF-SAMPLE TESTED
    ↓
ROBUSTNESS TESTED
    ↓
STATISTICALLY EVALUATED
    ↓
MULTIPLE-TESTING AWARE
    ↓
RESEARCH CANDIDATE
    ↓
PAPER VALIDATION
    ↓
EXECUTION VALIDATION
    ↓
LIVE — FUTURE PHASE ONLY
```

---

# 89. FINAL CURSOR INSTRUCTION

**START BY INSPECTING THE EXISTING QUANT LAB REPOSITORY.**

Do not assume the current structure matches this prompt exactly.

Determine:

```text
what already exists
what is incomplete
what should be extended
what should not be duplicated
```

Then implement Prompt 05 incrementally.

Use this order:

```text
INSPECT
  ↓
ARCHITECTURE RECONCILIATION
  ↓
BACKTEST CONTRACT
  ↓
PERFORMANCE ENGINE
  ↓
WALK-FORWARD
  ↓
PURGE + EMBARGO
  ↓
COST / SLIPPAGE
  ↓
ROBUSTNESS
  ↓
STATISTICS
  ↓
MULTIPLE TESTING
  ↓
RESEARCH GATE
  ↓
EXPERIMENT LINEAGE
  ↓
CLI
  ↓
DESKTOP INTEGRATION
  ↓
TESTS
  ↓
DOCUMENTATION
  ↓
FULL VALIDATION
```

After implementation, run:

```text
tests
ruff
mypy --strict
synthetic slice
desktop smoke tests
research-integrity tests
```

Report:

```text
files changed
architecture changes
new abstractions
new tests
validation results
known limitations
NOT_TESTED items
```

Do not report a feature as complete if it is only scaffolded.

Do not fabricate statistical results.

Do not fabricate benchmark data.

Do not fabricate real Indian-market data.

Do not silently weaken existing safety gates.

---

# 90. FINAL DESIGN PRINCIPLE

QUANT LAB must evolve from:

```text
"Can we backtest this?"
```

to:

```text
"Can we prove that this result deserves to be believed?"
```

The laboratory's most valuable output is not a profitable backtest.

It is a **reproducible, falsifiable, statistically disciplined conclusion about whether an apparent market effect is likely to be real, robust, and economically meaningful.**

Build Prompt 05 accordingly.
