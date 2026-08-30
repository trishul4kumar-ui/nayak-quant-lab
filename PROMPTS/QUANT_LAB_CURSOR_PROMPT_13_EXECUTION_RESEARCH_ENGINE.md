# QUANT LAB — CURSOR IMPLEMENTATION PROMPT 13
## Market Microstructure, Transaction Cost, Liquidity & Execution Simulation Engine
### Target Release: QUANT LAB 1.3.0

---

# 0. MISSION

You are implementing **Prompt 13** in the existing QUANT LAB repository.

QUANT LAB is already a research-grade, local-first quantitative research laboratory through Prompt 12 / version 1.2.0.

Your task is to add a **Market Microstructure, Transaction Cost, Liquidity & Execution Simulation Engine**.

The purpose is NOT to create another backtester.

The purpose is to answer a harder research question:

> **If an apparent statistical edge exists, can it survive realistic market mechanics, liquidity constraints, transaction costs, slippage, latency, participation, spread, and execution uncertainty?**

This layer must connect research outputs to executable economic reality without introducing look-ahead bias, survivorship bias, fabricated market data, or a second portfolio/backtest engine.

The implementation must be engineered as if QUANT LAB is intended to become a serious institutional quantitative research platform.

---

# 1. NON-NEGOTIABLE ARCHITECTURAL RULE

Do NOT rewrite or duplicate existing infrastructure.

Existing canonical components remain authoritative:

- Prompt 04 → Point-in-Time Data Fabric
- Prompt 05 → Research-Grade Backtesting & Validation Engine
- Prompt 06 → Feature & Alpha Research
- Prompt 07 → Cross-Sectional Alpha + Portfolio Construction
- Prompt 08 → Risk + Factor Research
- Prompt 09 → Regime + Temporal Dynamics
- Prompt 10 → Adaptive Alpha + Online Learning
- Prompt 11 → Statistical Learning
- Prompt 12 → Ensemble + Meta-Alpha
- Existing `run_backtest` → ONLY canonical portfolio simulation engine
- Existing covariance engine → ONLY canonical covariance implementation
- Existing Research Gate → ONLY promotion authority
- Existing Experiment Ledger → ONLY experiment provenance authority
- Existing `LiveSafetyGates` → ONLY live-safety authority

Prompt 13 must be a **simulation/research layer around the existing execution/backtest architecture**, not a replacement.

No second backtester.
No second portfolio constructor.
No second risk engine.
No broker implementation.
No live order path.

---

# 2. CORE CONCEPTUAL SEPARATION

Maintain these distinctions everywhere:

```text
DATA
≠
FEATURE
≠
FACTOR
≠
ALPHA
≠
MODEL
≠
ENSEMBLE
≠
REGIME
≠
TARGET PORTFOLIO
≠
ORDER INTENT
≠
EXECUTION MODEL
≠
FILL
≠
TRANSACTION COST
≠
REALIZED P&L
```

In particular:

```text
Portfolio target
      ↓
Order intent
      ↓
Execution simulation
      ↓
Fills
      ↓
Costs
      ↓
Position transition
      ↓
Realized execution P&L
```

A portfolio target is NOT an order.

An order intent is NOT a fill.

A simulated fill is NOT a broker-confirmed fill.

A transaction-cost estimate is NOT a guaranteed cost.

---

# 3. RESEARCH QUESTION

The engine must support investigation of:

1. How much of gross alpha survives execution?
2. How sensitive is performance to spread?
3. How sensitive is performance to slippage?
4. How much turnover can the strategy economically tolerate?
5. What fraction of ADV is being consumed?
6. Does participation become unrealistic?
7. How does latency affect execution?
8. What happens under adverse price movement?
9. What happens when an order cannot be fully filled?
10. What happens under partial fills?
11. What happens when liquidity disappears?
12. Does the alpha survive conservative execution assumptions?
13. Which components of transaction cost dominate?
14. What capacity does a strategy have?
15. Which strategies are execution-fragile?
16. Does the conclusion survive across regimes?

---

# 4. NEW PACKAGE

Create:

```text
src/quantlab/execution_research/
```

Suggested modules:

```text
execution_research/
├── __init__.py
├── schemas.py
├── market_microstructure.py
├── spread.py
├── slippage.py
├── impact.py
├── latency.py
├── liquidity.py
├── participation.py
├── fills.py
├── costs.py
├── capacity.py
├── simulator.py
├── scenarios.py
├── sensitivity.py
├── attribution.py
├── diagnostics.py
├── validation.py
└── errors.py
```

Keep `__init__.py` thin.

Do not create circular imports.

Do not import brokers.

Do not import UI modules.

Do not make this package responsible for portfolio construction.

---

# 5. POINT-IN-TIME REQUIREMENT

Every execution-research input must obey:

```text
available_time <= decision_time
```

Never use information that was unavailable when the decision was made.

This applies to:

- price
- bid
- ask
- spread
- volume
- ADV
- volatility
- liquidity
- participation assumptions
- market impact parameters
- latency assumptions
- regime information
- execution constraints

If an input is unavailable at T:

```text
None / unavailable
```

NOT:

```text
0
```

NOT:

```text
forward fill without documented validity
```

NOT:

```text
today's value
```

---

# 6. DATA HONESTY

Do NOT invent:

- NSE bid/ask history
- order-book depth
- official ADV
- official market-impact coefficients
- tick-by-tick market data
- broker execution statistics
- official exchange holidays
- hidden liquidity
- institutional execution data

The repository may contain synthetic execution scenarios for architecture tests.

Synthetic execution data MUST be explicitly labelled:

```text
data_kind = synthetic
```

Synthetic results must never be presented as market evidence.

If a required real-world input does not exist:

```text
NOT_TESTED
```

is the correct state.

Never convert missing calibration into an assumed PASS.

---

# 7. MARKET MICROSTRUCTURE MODEL

Implement a versioned `MarketMicrostructureDefinition`.

Minimum conceptual fields:

```text
spread_model
tick_size
bid_ask_availability
volume_model
liquidity_model
impact_model
latency_model
fill_model
participation_model
```

The definition must have:

```text
definition_id
version
formula
parameters
parameter_provenance
snapshot_id
config_hash
created_at
```

Identity must be immutable.

Changing a formula or parameter set requires a new version.

---

# 8. SPREAD MODELS

Implement research models such as:

### 8.1 Fixed spread

```text
spread_bps = constant
```

### 8.2 Volatility-scaled spread

Spread varies with volatility.

### 8.3 Volume/liquidity-scaled spread

Spread varies with available liquidity.

### 8.4 Configured historical spread

Only if actual PIT bid/ask data exists.

If not available:

```text
NOT_TESTED
```

Do not fabricate historical spreads.

---

# 9. SLIPPAGE MODELS

Implement versioned slippage models:

```text
none
fixed_bps
spread_fraction
volatility_scaled
volume_scaled
configured
```

All assumptions must be explicit.

Example:

```text
execution_price =
reference_price
± spread_component
± slippage_component
± impact_component
```

Direction must be correct:

```text
BUY  → higher execution price
SELL → lower execution price
```

Never allow sign mistakes to artificially improve execution.

---

# 10. MARKET IMPACT

Implement research-grade impact abstractions.

At minimum support:

### 10.1 Fixed impact

```text
impact_bps = constant
```

### 10.2 Square-root impact research model

Support a configurable form conceptually equivalent to:

```text
impact ∝ volatility × sqrt(order_size / available_volume)
```

Parameters must be explicit and versioned.

### 10.3 Participation-based impact

Impact increases as:

```text
order_size / available_volume
```

increases.

The implementation must NOT claim that the coefficients are empirically calibrated unless actual calibration data exists.

Label uncalibrated impact:

```text
UNCALIBRATED
```

and keep the research result appropriately gated.

---

# 11. LATENCY MODEL

Implement explicit latency.

Latency can exist between:

```text
decision_time
→ signal_generation
→ order_submission
→ market_arrival
→ execution
```

Support:

```text
zero
fixed
configured
scenario_distribution
```

Do not use future prices to determine the latency itself.

A latency scenario must shift execution availability forward.

Example:

```text
decision at T
latency = Δt
eligible execution begins at T + Δt
```

No fill before market arrival.

---

# 12. ORDER INTENT

Create a research-level immutable `OrderIntent`.

It must include at minimum:

```text
intent_id
decision_time
security_id
side
target_quantity
reference_price
portfolio_id
strategy_id
alpha_id
model_id
ensemble_id
urgency
max_participation
limit_price (optional)
time_in_force
```

This is a research object.

It must NOT be sent to a broker.

---

# 13. ORDER SIZING

Execution research must consume target portfolio changes generated by the existing portfolio layer.

Example:

```text
target_weight
      ↓
current_weight
      ↓
target_delta
      ↓
desired_quantity
      ↓
OrderIntent
```

Do not create a second portfolio optimizer.

Do not silently modify target weights.

If an execution constraint prevents full execution, report the residual.

---

# 14. PARTICIPATION MODEL

Implement:

```text
participation_rate =
executed_quantity / available_volume
```

Support configurable maximum participation:

```text
max_participation
```

Example scenarios:

```text
5%
10%
20%
30%
```

If available volume is unknown:

```text
capacity = NOT_TESTED
```

Do not assume infinite liquidity.

---

# 15. PARTIAL FILLS

Partial fills are mandatory.

A simulated order may result in:

```text
fully_filled
partially_filled
unfilled
```

The engine must preserve:

```text
requested_quantity
filled_quantity
remaining_quantity
fill_ratio
```

Never silently convert an unfilled order into a full fill.

---

# 16. FILL MODEL

Create immutable `SimulatedFill`.

Minimum fields:

```text
fill_id
intent_id
security_id
timestamp
side
quantity
reference_price
execution_price
spread_cost
slippage_cost
impact_cost
explicit_cost
total_cost
fill_status
model_id
```

A fill must be reproducible from:

```text
dataset snapshot
execution model
config hash
seed
```

---

# 17. EXECUTION PRICE DECOMPOSITION

Every simulated fill must permit attribution:

```text
Reference Price
      +
Spread
      +
Slippage
      +
Market Impact
      +
Explicit Transaction Costs
      =
Executed Economic Price
```

For sells, preserve economically correct signs.

Do not collapse all costs into a single unexplained number.

---

# 18. TRANSACTION COST MODEL

Implement explicit cost components.

At minimum:

```text
brokerage
exchange_fees
taxes
regulatory_fees
stamp_duty
spread
slippage
impact
```

Do NOT invent current Indian fee schedules.

Reuse the existing Prompt 05 `CostSchedule` where appropriate.

Prompt 13 must extend/reuse the existing cost abstraction rather than create a conflicting cost system.

Each component must carry:

```text
value
unit
provenance
status
```

Example:

```text
status =
CALIBRATED
CONFIGURED
UNSPECIFIED
NOT_TESTED
```

---

# 19. INDIAN MARKET SUPPORT

Design the schema so the engine can eventually support Indian markets, including:

- NSE equities
- BSE equities
- equity intraday
- delivery
- ETFs
- futures
- options

But do NOT fabricate exchange-specific data.

The first implementation may support a generic equity execution model.

India-specific fee/tax modules should be explicit and independently versioned when real source data becomes available.

---

# 20. LIQUIDITY MODEL

Implement a `LiquidityProfile`.

Possible fields:

```text
ADV
median_volume
volume_percentile
turnover
spread
participation_limit
liquidity_bucket
capacity
```

Every liquidity quantity must be PIT-valid.

Do not calculate today's ADV and apply it to historical T.

---

# 21. CAPACITY ANALYSIS

The engine must estimate research capacity.

At minimum test:

```text
capital =
₹1 lakh
₹10 lakh
₹50 lakh
₹1 crore
₹5 crore
₹10 crore
```

These are scenario inputs, not claims.

Capacity analysis should answer:

```text
At what capital level does:
- participation exceed threshold?
- impact become excessive?
- fill ratio deteriorate?
- expected net alpha disappear?
```

Do not state that a strategy has a specific real-world capacity unless calibrated data supports it.

---

# 22. EXECUTION SCENARIOS

Implement scenario definitions.

Examples:

```text
BASE
CONSERVATIVE
HIGH_SLIPPAGE
WIDE_SPREAD
HIGH_IMPACT
LOW_LIQUIDITY
HIGH_LATENCY
PARTIAL_FILL
STRESSED
```

Each scenario must be versioned.

A scenario is not a forecast.

It is a controlled stress experiment.

---

# 23. EXECUTION SENSITIVITY

Implement sensitivity analysis over:

```text
spread_bps
slippage_bps
impact_coefficient
latency
participation_limit
fill_ratio
capital
turnover
```

Output should show:

```text
gross return
execution cost
net return
cost drag
turnover
fill ratio
participation
max impact
capacity
drawdown
Sharpe
```

Do not optimize parameters to produce a desired answer.

Sensitivity analysis is diagnostic.

---

# 24. COST ATTRIBUTION

Implement:

```text
total_execution_cost
├── spread_cost
├── slippage_cost
├── impact_cost
├── explicit_cost
└── other_configured_cost
```

Support attribution by:

```text
strategy
alpha
model
ensemble
security
day
regime
execution scenario
```

All aggregation must preserve lineage.

---

# 25. REGIME-CONDITIONAL EXECUTION

Integrate with Prompt 09.

Research execution behaviour conditional on:

```text
trend
volatility
correlation
regime
```

Example research questions:

```text
Does momentum suffer higher execution cost during high-volatility regimes?

Does turnover become uneconomic during stressed regimes?

Does liquidity-adjusted capacity collapse during certain states?
```

Do not use hindsight regime labels.

Use only predictive-safe regime definitions.

---

# 26. ALPHA-TO-EXECUTION ATTRIBUTION

Integrate with Prompts 06, 07, 08, 10, 11, and 12.

The system should be able to decompose:

```text
Gross Alpha
      ↓
Portfolio Construction
      ↓
Turnover
      ↓
Execution Friction
      ↓
Net Alpha
```

Research output:

```text
gross_signal_edge
portfolio_edge
spread_drag
slippage_drag
impact_drag
explicit_cost_drag
net_edge
```

This must NOT modify the alpha itself.

---

# 27. EXECUTION FRAGILITY SCORE

Implement a research diagnostic:

```text
ExecutionFragility
```

It should consider sensitivity to:

- spread
- slippage
- impact
- latency
- participation
- liquidity
- fill ratio

Do NOT pretend this is a universally calibrated probability.

It is a deterministic research metric whose formula is documented and versioned.

---

# 28. RESEARCH GATE INTEGRATION

Prompt 05 remains the only promotion gate.

Prompt 13 must feed execution diagnostics into the existing gate.

Examples:

```text
execution_data_missing
uncalibrated_impact
unknown_liquidity
partial_fill_not_tested
latency_not_tested
spread_not_tested
capacity_not_tested
```

These should remain explicit.

A strategy must not be promoted simply because gross backtest performance is strong.

Example conceptual rule:

```text
gross_alpha strong
+
execution realism weak
=
WARN / NOT_READY
```

Never silently treat missing execution realism as PASS.

---

# 29. NEW INTEGRITY CHECKS

Add explicit integrity checks for:

```text
future_volume_leak
future_spread_leak
future_liquidity_leak
future_impact_parameter
future_execution_parameter
future_latency
pre_arrival_fill
full_fill_assumption
zero_cost_execution
negative_execution_cost
wrong_side_slippage
wrong_side_impact
hidden_partial_fill
capacity_lookahead
execution_model_mutation
future_execution_calibration
```

Required semantics:

```text
FAIL
```

for direct leakage.

```text
NOT_TESTED
```

for missing evidence.

Never turn:

```text
NOT_TESTED → PASS
```

automatically.

---

# 30. RANDOMNESS AND REPRODUCIBILITY

If execution models contain stochastic components:

- require explicit seed
- store seed in experiment identity
- store model version
- store scenario version
- store dataset snapshot
- store configuration hash

Same inputs must reproduce the same result when deterministic mode is selected.

Support Monte Carlo execution scenarios where appropriate, but clearly separate:

```text
historical observation
vs
simulation assumption
```

---

# 31. MONTE CARLO EXECUTION

Implement an optional research layer for execution uncertainty.

Possible perturbations:

```text
slippage
latency
fill ratio
spread
impact
volume
```

Run multiple execution paths.

Report:

```text
mean net return
median net return
5th percentile
25th percentile
75th percentile
95th percentile
probability net edge < 0
```

This is a simulation distribution, NOT a confidence interval unless statistically justified.

Do not confuse Monte Carlo execution uncertainty with statistical alpha significance.

---

# 32. CLI

Add:

```bash
quantlab execution list
quantlab execution inspect <id>
quantlab execution simulate <experiment>
quantlab execution report <id>

quantlab execution spread <experiment>
quantlab execution slippage <experiment>
quantlab execution impact <experiment>
quantlab execution liquidity <experiment>
quantlab execution latency <experiment>
quantlab execution fills <experiment>

quantlab execution costs <experiment>
quantlab execution attribution <experiment>
quantlab execution sensitivity <experiment>
quantlab execution capacity <experiment>
quantlab execution stress <experiment>

quantlab research execution
quantlab research execution-cost
quantlab research execution-fragility
quantlab research capacity
```

CLI must call `quantlab.app` services.

No business logic in CLI.

---

# 33. DESKTOP INTEGRATION

Extend the existing desktop application.

Add:

```text
Execution Lab
```

Navigation:

```text
Execution
├── Overview
├── Cost Breakdown
├── Slippage
├── Impact
├── Liquidity
├── Latency
├── Fills
├── Capacity
├── Sensitivity
├── Stress Tests
└── Attribution
```

Architecture:

```text
Qt UI
  ↓
quantlab.app
  ↓
execution research services
  ↓
existing data / portfolio / backtest / ledger
```

The UI must NOT:

- read Parquet directly
- calculate impact
- fit models
- manipulate fills
- modify experiments
- bypass research gate
- access brokers

---

# 34. EXPERIMENT LEDGER

Every execution experiment must record:

```text
experiment_id
dataset_id
snapshot_checksum
data_kind
execution_model_id
execution_model_version
scenario_id
scenario_version
portfolio_id
strategy_id
alpha_id
model_id
ensemble_id
config_hash
random_seed
timestamp
integrity_status
gate_outcome
```

The existing experiment ledger remains canonical.

Do not create another ledger.

---

# 35. API / SERVICE LAYER

Expose execution research through `quantlab.app`.

Suggested service methods:

```text
list_execution_models()
inspect_execution_model()
simulate_execution()
execution_report()
cost_attribution()
execution_sensitivity()
capacity_analysis()
execution_stress()
execution_fragility()
execution_integrity()
```

The application layer orchestrates.

Domain modules calculate.

UI only presents.

---

# 36. DOCUMENTATION

Create:

```text
docs/architecture/EXECUTION_RESEARCH_ENGINE.md
docs/architecture/MARKET_MICROSTRUCTURE.md
docs/research/EXECUTION_COST_RESEARCH.md
docs/research/SLIPPAGE_RESEARCH.md
docs/research/MARKET_IMPACT.md
docs/research/LIQUIDITY_AND_CAPACITY.md
docs/research/EXECUTION_LATENCY.md
docs/research/EXECUTION_FRAGILITY.md
docs/decisions/ADR-027-execution-research-engine.md
```

Document formulas, assumptions, units, provenance, limitations, and failure modes.

---

# 37. TESTING REQUIREMENTS

Add comprehensive tests.

Minimum categories:

```text
tests/execution_research/
├── test_spread.py
├── test_slippage.py
├── test_impact.py
├── test_latency.py
├── test_liquidity.py
├── test_participation.py
├── test_fills.py
├── test_costs.py
├── test_capacity.py
├── test_scenarios.py
├── test_attribution.py
├── test_sensitivity.py
├── test_integrity.py
├── test_reproducibility.py
└── test_e2e.py
```

Test:

### Directionality

BUY costs must not improve execution.

SELL costs must not improve execution.

### Latency

No fill may occur before market arrival.

### Participation

Filled quantity cannot exceed configured available volume/participation constraints.

### Partial fill

Remaining quantity is preserved.

### Cost decomposition

Components sum correctly to total execution cost.

### PIT

Future volume/spread/liquidity cannot affect historical execution.

### Reproducibility

Same seed + same inputs = same simulation.

### Stress

Increasing friction should not systematically improve net performance.

### Zero-cost

Execution with zero cost must be explicitly marked as unrealistic research mode, not production-like.

### Synthetic

Synthetic execution results cannot promote.

---

# 38. PROPERTY-BASED TESTS

Where practical, implement properties such as:

```text
higher spread → non-lower execution cost

higher slippage → non-lower execution cost

higher impact → non-lower execution cost

higher latency → never earlier fill

lower participation → never more filled quantity

requested_quantity >= filled_quantity

filled_quantity + remaining_quantity == requested_quantity
```

Be careful with models where nonlinear behaviour makes a strict monotonicity assumption invalid; document exceptions.

---

# 39. STATIC QUALITY

Before completion:

```bash
ruff check .
mypy --strict src/quantlab
pytest
```

All must pass.

Do not weaken typing to make implementation pass.

Do not suppress lint/type errors without documented justification.

---

# 40. BACKWARD COMPATIBILITY

Existing commands must remain functional:

```bash
quantlab slice
quantlab backtest ...
quantlab validate ...
quantlab research ...
quantlab feature ...
quantlab alpha ...
quantlab portfolio ...
quantlab factor ...
quantlab risk ...
quantlab regime ...
quantlab adaptive ...
quantlab model ...
quantlab ensemble ...
quantlab desktop
```

Prompt 01–12 tests must continue passing.

Do not alter:

```text
next-bar fill semantics
10 bps default baseline
PIT available_time <= as_of
risk firewall
research gate
experiment ledger
LIVE_TRADING=false
```

---

# 41. LIVE TRADING SAFETY

This is critical.

Prompt 13 must NOT create:

```text
broker connection
order submission
live execution
Zerodha API execution
OpenAlgo execution
```

Execution simulation is not execution.

All simulated objects must remain research objects.

Verify:

```python
LiveSafetyGates().live_trading is False
```

AI cannot:

```text
REQUEST_LIVE_ORDER
OVERRIDE_RESEARCH_GATE
```

No new code path may bypass this.

---

# 42. ARCHITECTURAL BOUNDARY

Maintain:

```text
quantlab.execution_research
        ↓
research simulation only
```

NOT:

```text
quantlab.execution_research
        ↓
broker
```

The future architecture may eventually become:

```text
Research
   ↓
Paper OMS
   ↓
Reconciliation
   ↓
Broker Adapter
   ↓
Live Trading
```

But Prompt 13 must stop before that boundary.

---

# 43. NO SECOND BACKTESTER

This is an explicit acceptance criterion.

DO NOT implement:

```text
ExecutionBacktester
MicrostructureBacktester
ExecutionPortfolioSimulator
```

Instead:

```text
existing run_backtest()
        +
execution simulation layer
        +
execution-aware diagnostics
```

If changes to `run_backtest()` are required, make the smallest backward-compatible extension and document it in ADR-027.

---

# 44. RESEARCH OUTPUT

A completed execution experiment should produce a structured report approximately like:

```text
Experiment
├── Dataset
├── PIT Integrity
├── Strategy
├── Portfolio
├── Execution Model
├── Scenario
├── Gross Performance
├── Execution Costs
│   ├── Spread
│   ├── Slippage
│   ├── Impact
│   └── Explicit Costs
├── Fill Statistics
├── Participation
├── Liquidity
├── Capacity
├── Latency
├── Net Performance
├── Execution Fragility
├── Regime Conditionality
├── Sensitivity
├── Monte Carlo
├── Integrity
└── Research Gate
```

---

# 45. EXECUTION-AWARE RESEARCH GATE

The system should distinguish:

```text
GROSS_EDGE
EXECUTION_ADJUSTED_EDGE
NET_EDGE
```

A strong gross result with weak execution evidence must not be treated as a strong strategy.

Conceptually:

```text
Gross alpha
    ↓
Execution model
    ↓
Net alpha
    ↓
Statistical validation
    ↓
Robustness
    ↓
Capacity
    ↓
Research Gate
```

Prompt 05 remains authoritative for final promotion.

---

# 46. REQUIRED SYNTHETIC VALIDATION EXPERIMENT

Create a deterministic synthetic execution fixture.

It should contain:

```text
multiple securities
known volume
known spread
known volatility
known target weights
multiple rebalances
partial-fill opportunity
latency scenario
impact scenario
```

Demonstrate:

1. Gross portfolio performance exists.
2. Execution costs reduce net performance under normal assumptions.
3. Increasing spread increases cost.
4. Increasing impact increases cost.
5. Lower participation changes fill behaviour.
6. Latency delays fills.
7. Partial fills preserve residual orders.
8. Capacity eventually deteriorates.
9. Future liquidity cannot alter historical fills.
10. Synthetic result remains `WARN`.

The experiment is an architecture test, NOT alpha evidence.

---

# 47. DEFINITION OF DONE

Prompt 13 is complete only when all of the following are true:

### Architecture

- [ ] `quantlab.execution_research` exists
- [ ] No second backtester
- [ ] No broker imports
- [ ] Existing architecture preserved
- [ ] ADR-027 created

### Microstructure

- [ ] Spread models
- [ ] Slippage models
- [ ] Impact models
- [ ] Latency models
- [ ] Liquidity model
- [ ] Participation model
- [ ] Partial fills
- [ ] Execution price decomposition

### Costs

- [ ] Explicit cost decomposition
- [ ] Reuse/extension of Prompt 05 costs
- [ ] Provenance
- [ ] India-ready schema without fabricated fees

### Research

- [ ] Execution simulation
- [ ] Cost attribution
- [ ] Sensitivity
- [ ] Stress scenarios
- [ ] Capacity
- [ ] Execution fragility
- [ ] Regime conditionality
- [ ] Monte Carlo execution uncertainty

### Integrity

- [ ] PIT enforcement
- [ ] Future liquidity leak detection
- [ ] Future spread leak detection
- [ ] Future execution parameter leak detection
- [ ] Pre-arrival fill detection
- [ ] Wrong-side cost detection
- [ ] Full-fill assumption detection
- [ ] Capacity look-ahead detection

### Desktop

- [ ] Execution Lab
- [ ] Query/service architecture
- [ ] No domain logic in Qt

### CLI

- [ ] Execution commands
- [ ] Research commands

### Ledger

- [ ] Execution experiments recorded
- [ ] Dataset checksum recorded
- [ ] Model/scenario identity recorded
- [ ] Configuration hash recorded
- [ ] Seed recorded

### Safety

- [ ] `LIVE_TRADING=false`
- [ ] No broker imports
- [ ] AI cannot request live orders
- [ ] AI cannot override gate

### Quality

- [ ] Full pytest passes
- [ ] Prompt 01–12 tests pass
- [ ] Ruff passes
- [ ] Mypy strict passes
- [ ] UI offscreen smoke passes

---

# 48. REQUIRED FINAL REPORT FROM CURSOR

When implementation is complete, report:

```text
QUANT LAB VERSION:
PROMPT 13 STATUS:

FILES CREATED:
FILES MODIFIED:

NEW MODULES:

NEW CLI COMMANDS:

NEW DESKTOP FEATURES:

EXECUTION MODELS:

COST MODELS:

IMPACT MODELS:

LATENCY MODELS:

LIQUIDITY/CAPACITY:

INTEGRITY CHECKS:

TEST COUNT:
RUFF:
MYPY:

PIT STATUS:

SYNTHETIC EXECUTION RESULT:

RESEARCH GATE RESULT:

NOT_TESTED:

LIVE_TRADING:

BROKER IMPORT CHECK:

BACKWARD COMPATIBILITY:

ADR:
DOCUMENTATION:

KNOWN LIMITATIONS:
```

Do not claim completion without actually running the verification suite.

---

# 49. FINAL ENGINEERING PRINCIPLE

The objective of Prompt 13 is NOT:

> “Make backtests look realistic.”

The objective is:

> **Determine whether an apparent statistical edge remains economically meaningful after realistic execution friction, liquidity constraints, and uncertainty are applied.**

QUANT LAB must be capable of discovering that:

```text
alpha exists statistically
        ↓
but
        ↓
execution destroys it
```

and treating that as a **successful research conclusion**.

The strongest possible outcome is not the highest simulated return.

The strongest outcome is a reproducible answer to:

> **What information existed at T, what position did the research process request, what could realistically have been executed, what did it cost, what remained after execution, and does that residual edge survive rigorous validation?**

That is the standard Prompt 13 must implement.

# END OF PROMPT 13
