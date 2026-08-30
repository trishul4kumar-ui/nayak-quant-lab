# QUANT LAB — PROMPT 21
# Institutional Transaction Cost Analysis, Execution Calibration, Liquidity & Capacity Engine

**Target release:** QUANT LAB 2.1.0  
**Depends on:** Prompts 01–20  
**Primary objective:** Determine whether a strategy survives realistic execution, quantify implementation shortfall, calibrate execution models from legitimate evidence, and estimate scalable capacity without fabricating liquidity.

## 0. CODING-AGENT DIRECTIVE

Before implementation:

1. Inspect Prompts 01–20 completely.
2. Inspect Prompt 13 execution research.
3. Inspect Prompt 18 Paper OMS.
4. Inspect Prompt 19 monitoring/performance architecture.
5. Inspect Prompt 20 data contracts.
6. Reuse canonical cost, execution, liquidity and risk interfaces.
7. Do not build a second backtester.
8. Do not build a second execution simulator.
9. Do not import brokers.
10. Do not fabricate bid/ask, depth, ADV, impact coefficients or Indian fee schedules.

This prompt is **research/calibration infrastructure**, not live trading.

## 1. CORE QUESTION

The engine must answer:

> **How much of an observed trading edge survives the actual execution environment, and at what capital scale does the strategy become economically fragile?**

Distinguish:

```text
SIGNAL EDGE
→ TARGET PORTFOLIO
→ ORDER INTENT
→ EXPECTED EXECUTION
→ ACTUAL/SIMULATED FILL
→ COST
→ IMPLEMENTATION SHORTFALL
→ NET EDGE
→ CAPACITY
```

## 2. ARCHITECTURE

```text
TARGET PORTFOLIO
      ↓
ORDER INTENT
      ↓
PAPER / EXECUTION OBSERVATION
      ↓
TCA
 ├── spread
 ├── slippage
 ├── commissions
 ├── taxes/fees when sourced
 ├── impact
 ├── latency
 ├── partial fills
 └── opportunity cost
      ↓
IMPLEMENTATION SHORTFALL
      ↓
CALIBRATED EXECUTION MODEL
      ↓
CAPACITY / FRAGILITY
      ↓
RESEARCH FEEDBACK
```

Prompt 21 wraps Prompt 13 models; it does not replace them.

## 3. REQUIRED PACKAGE

Create:

```text
src/quantlab/tca/
```

Suggested modules:

```text
models.py
benchmarks.py
spread.py
slippage.py
impact.py
latency.py
fills.py
shortfall.py
costs.py
liquidity.py
capacity.py
calibration.py
estimation.py
uncertainty.py
fragility.py
sensitivity.py
stress.py
attribution.py
repository.py
service.py
identity.py
integrity.py
cli.py
library.py
errors.py
enums.py
__init__.py
```

Thin `__init__.py`.

## 4. TCA DEFINITIONS

Implement explicit definitions for:

### Arrival Price

Price observable at the legitimate decision/arrival boundary.

### Decision Price

Price used when the investment decision was frozen.

### Execution Price

Actual/simulated fill price.

### VWAP/TWAP

Only when the required observations exist.

### Implementation Shortfall

At minimum decompose:

```text
IS =
delay cost
+ trading cost
+ spread cost
+ market impact
+ opportunity cost
+ explicit fees
```

Definitions must be versioned.

## 5. NO FAKE BENCHMARKS

Benchmark hierarchy:

1. legitimate event-time/arrival price
2. user-supplied benchmark
3. bar-derived benchmark when explicitly labelled
4. unavailable

Never substitute future prices merely because they make TCA easier.

## 6. SPREAD ANALYSIS

Support:

- quoted spread when bid/ask exists
- effective spread
- realized spread where valid
- bar-derived proxy only when explicitly labelled

Do not infer a real bid/ask spread from OHLC and call it observed.

Missing microstructure data:

```text
NOT_TESTED
```

## 7. SLIPPAGE

Reuse Prompt 13.

Support:

```text
fixed_bps
spread_relative
configured
observed
```

Decompose:

```text
buy slippage = execution_price - benchmark_price
sell slippage = benchmark_price - execution_price
```

Direction must be explicit.

Wrong-side calculations → `FAIL`.

## 8. MARKET IMPACT

Support research models:

### Fixed

```text
impact = k
```

### Square-root

```text
impact ∝ volatility × sqrt(Q / V)
```

### Participation

```text
impact ∝ Q / V
```

All coefficients must carry:

```text
source
fit_window
universe
frequency
calibration_method
sample_count
confidence/uncertainty
```

No coefficient may silently become “empirical.”

## 9. CALIBRATION

This is the central addition.

Calibrate execution models only from valid observations.

Potential inputs:

```text
order quantity
executed quantity
arrival price
execution price
volume
volatility
spread
participation
latency
side
security
session
```

Training/calibration windows must obey PIT.

Use:

```text
CALIBRATE → FREEZE → TEST
```

Never:

```text
FIT ON ALL DATA → REPLAY HISTORY
```

## 10. STATISTICAL ESTIMATION

Where appropriate support:

- robust regression
- quantile regression
- binned participation analysis
- log-log impact estimation
- bootstrap uncertainty
- outlier diagnostics
- heteroskedasticity-aware inference

Avoid unnecessary ML.

If sample size is insufficient:

```text
NOT_TESTED
```

Do not fit an impressive-looking model to inadequate data.

## 11. EXECUTION UNCERTAINTY

Every calibrated parameter should have:

```text
estimate
uncertainty
sample_count
coverage
date_range
source
calibration_hash
```

Prefer ranges to false precision.

Example:

```text
impact coefficient = estimate ± uncertainty
```

not a naked coefficient.

## 12. LIQUIDITY

Measure where data exists:

- volume
- turnover
- participation
- spread
- traded/notional volume
- rolling volume
- liquidity percentile

Do not call synthetic volume “NSE ADV.”

Missing volume means:

```text
capacity = NOT_TESTED
```

not infinite capacity.

## 13. CAPACITY ENGINE

Estimate strategy capacity under explicit assumptions.

Scenarios should vary:

```text
portfolio capital
order participation
max participation
ADV
spread
impact coefficient
turnover
rebalance frequency
```

Example diagnostic ladder:

```text
₹1L
₹5L
₹10L
₹25L
₹50L
₹1Cr
₹5Cr
₹10Cr
```

These are scenario sizes, not claims.

Calculate:

- participation
- estimated impact
- expected cost
- net return degradation
- turnover
- residual/unfilled quantity
- capacity breach

## 14. CAPACITY DEFINITION

Do not define capacity as:

> “largest capital that still has positive backtest return.”

Instead define an explicit policy such as:

```text
maximum capital satisfying:
participation <= threshold
+
estimated cost <= threshold
+
expected net edge >= threshold
+
risk constraints remain feasible
```

All thresholds must be policy inputs.

## 15. EXECUTION FRAGILITY

Generate fragility surfaces across:

- spread
- slippage
- impact
- latency
- participation
- liquidity
- turnover
- capital

Output:

```text
ROBUST
FRAGILE
ECONOMICALLY_UNVIABLE
NOT_TESTED
```

Do not let fragility labels become automatic promotion decisions.

Prompt 05 remains the only research promotion gate.

## 16. PAPER OMS COMPARISON

Compare:

```text
TARGET
vs
PAPER ORDER
vs
PAPER FILL
vs
TCA EXPECTATION
```

Measure:

- target deviation
- execution deviation
- cost deviation
- residual
- partial-fill deviation
- timing deviation

Paper fill ≠ broker-confirmed fill.

## 17. REALIZED VS MODELLED TCA

Clearly distinguish:

```text
OBSERVED_TCA
MODELLED_TCA
CALIBRATED_TCA
STRESSED_TCA
```

Never report modelled costs as realized costs.

## 18. COST PROVENANCE

Reuse Prompt 05 `CostSchedule`.

Indian fees/taxes must be source-backed.

Until legitimate fee data is available:

```text
STT
STAMP
GST
SEBI
OTHER TAX LEGS
```

remain explicitly unspecified.

Never insert guessed Indian rates.

## 19. OPPORTUNITY COST

Where unfilled quantity exists, estimate opportunity cost only if a valid post-decision reference path is available.

Do not use future information in a way that contaminates a live-decision simulation.

Opportunity-cost analysis is measurement after the fact, not an input to the original decision.

## 20. INTEGRITY FLAGS

Add:

```text
future_tca_observation
future_impact_calibration
future_spread_calibration
future_volume_calibration
future_liquidity_calibration
future_capacity_parameter
arrival_price_lookahead
benchmark_price_lookahead
wrong_side_slippage
wrong_side_impact
posthoc_cost_model
model_replay_leak
calibration_window_leak
future_fill_observation
hidden_partial_fill
capacity_lookahead
synthetic_adv_claim
observed_vs_modelled_confusion
tca_parameter_mutation
```

Direct leakage → `FAIL`.

Unknown evidence → `NOT_TESTED`.

## 21. DETERMINISM

Same:

```text
execution observations
+ PIT snapshot
+ calibration window
+ model version
+ policy
```

must produce identical:

- coefficients
- diagnostics
- capacity scenarios
- fragility results
- hashes

## 22. MODEL VERSIONING

Every calibrated model requires:

```text
model_id
model_version
training/calibration snapshot
fit window
feature definition
parameter hash
data checksum
method
sample count
uncertainty
validation result
```

Changing a calibration parameter creates a new identity.

## 23. CLI

Implement:

```text
quantlab tca list
quantlab tca inspect <id>
quantlab tca run
quantlab tca spread
quantlab tca slippage
quantlab tca impact
quantlab tca shortfall
quantlab tca costs
quantlab tca latency
quantlab tca liquidity
quantlab tca calibrate
quantlab tca calibration-report
quantlab tca capacity
quantlab tca fragility
quantlab tca sensitivity
quantlab tca stress
quantlab tca compare
quantlab tca report
```

Research aliases:

```text
quantlab research tca
quantlab research implementation-shortfall
quantlab research execution-calibration
quantlab research capacity
quantlab research execution-fragility
```

## 24. DESKTOP

Add **TCA & Capacity Lab**.

Display:

- execution cost decomposition
- arrival vs execution
- slippage
- impact
- liquidity
- calibration status
- parameter uncertainty
- capacity curves
- fragility matrix
- paper-vs-model comparison
- NOT_TESTED warnings

Qt must only query `quantlab.app`.

No broker access.

## 25. TEST REQUIREMENTS

Minimum focused target: **70+ tests**.

Cover:

- buy/sell sign
- arrival benchmark
- spread
- slippage
- impact
- latency
- partial fills
- shortfall decomposition
- cost provenance
- PIT calibration
- calibration freeze
- uncertainty
- liquidity
- capacity
- fragility
- synthetic-vs-real labels
- deterministic hashes
- model identity
- Paper OMS comparison
- integrity leakage
- knowledge lineage
- ledger compatibility
- UI smoke

Adversarial tests must append future volume/spread/fills/calibration observations and prove historical TCA is unchanged.

## 26. KNOWLEDGE GRAPH

Record:

```text
TCA_RUN
EXECUTION_OBSERVATION
CALIBRATED_EXECUTION_MODEL
LIQUIDITY_OBSERVATION
CAPACITY_RESULT
FRAGILITY_RESULT
```

Link to:

- order intent
- paper order
- fill
- target portfolio
- performance
- experiment
- alpha
- research hypothesis

Failed calibration and capacity breaches must remain historical evidence.

## 27. LEDGER

Extend the existing ledger only.

Potential fields:

```text
tca_run_id
tca_hash
execution_model_id
calibration_hash
arrival_price_policy
shortfall
cost_decomposition
capacity_policy_id
capacity_result_id
fragility_status
```

No second ledger.

## 28. SAFETY

Prompt 21 must not import:

```text
kiteconnect
zerodha
openalgo
quantlab.brokers
```

No order routing.

No cancellation.

No live modification.

```text
LIVE_TRADING = false
```

## 29. NOT_TESTED

Do not fabricate:

- official NSE ADV
- historical order-book depth
- historical bid/ask
- tick-level execution
- institutional TCA
- broker execution reports
- calibrated Indian impact coefficients
- hidden liquidity
- queue position
- real latency distributions
- complete Indian fee/tax history

## 30. DEFINITION OF DONE

Prompt 21 is complete only when:

- Prompt 13 execution models are reused
- Prompt 18 paper observations are supported
- Prompt 19 performance links exist
- Prompt 20 PIT data contracts are honored
- calibration is PIT-safe
- calibration models are immutable/versioned
- uncertainty is reported
- capacity is policy-defined
- fragility is measurable
- observed/modelled TCA is clearly separated
- tests pass
- ruff clean
- mypy strict on owned code
- full regression passes
- Knowledge Graph lineage works
- ledger remains compatible
- desktop viewer works
- `LIVE_TRADING=false`
- no fabricated liquidity or cost evidence exists

## 31. FINAL PRINCIPLE

A strategy is not scalable merely because its backtest is profitable.

The system must be able to conclude:

> **“The alpha exists under the research assumptions, but the strategy becomes economically non-viable at this capital scale.”**

That is a successful research finding, not a failure.
