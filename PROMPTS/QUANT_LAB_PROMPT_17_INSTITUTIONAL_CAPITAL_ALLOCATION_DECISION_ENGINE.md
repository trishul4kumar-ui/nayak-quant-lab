# QUANT LAB — PROMPT 17
# Institutional-Grade Capital Allocation & Investment Decision Engine

**Target Version:** 1.7.0  
**Status:** ENGINEERING IMPLEMENTATION SPECIFICATION  
**Parent System:** QUANT LAB 1.6.0  
**Execution Boundary:** RESEARCH / DECISION ONLY  
**LIVE_TRADING:** MUST REMAIN `false`

---

## 0. MISSION

You are implementing **Prompt 17 — Institutional-Grade Capital Allocation & Investment Decision Engine** for QUANT LAB.

This is a production-oriented quantitative capital-allocation layer. It must transform validated research outputs into:

> **risk-aware, constraint-aware, capital-aware target portfolio decisions**

It must **NOT** place broker orders.

Prompt 17 sits after the research, validation, knowledge, factor, regime, adaptive-learning, model, ensemble, and execution-research layers, and immediately before the future Paper OMS / Broker Abstraction layers.

The engine must answer:

1. How much capital should be allocated?
2. Which validated opportunities deserve capital?
3. What portfolio-level risk budget should each receive?
4. What position sizes are mathematically justified?
5. Which constraints bind?
6. When should the system abstain?
7. What target portfolio should exist at decision time T?
8. Why did the engine make that decision?
9. Which research evidence, model, alpha, factor and risk assumptions produced it?
10. Is the decision reproducible exactly from the frozen PIT snapshot and configuration?

The engine must **never** answer:

> "Send this order to Zerodha."

That belongs to future execution infrastructure.

---

# 1. NON-NEGOTIABLE ARCHITECTURAL PRINCIPLES

Preserve all previous QUANT LAB architecture.

There must remain:

- ONE PIT data fabric
- ONE canonical backtester
- ONE covariance engine
- ONE research gate
- ONE risk firewall
- ONE experiment ledger
- ONE research knowledge system
- ONE execution-research layer
- ONE canonical portfolio-construction layer
- ZERO broker imports in Prompt 17

Do not create competing implementations.

### Mandatory conceptual separation

```text
DATA
≠ FEATURE
≠ FACTOR
≠ ALPHA
≠ REGIME
≠ MODEL
≠ ADAPTIVE LEARNER
≠ ENSEMBLE
≠ PORTFOLIO
≠ RISK
≠ CAPITAL ALLOCATION
≠ INVESTMENT DECISION
≠ ORDER INTENT
≠ ORDER
≠ EXECUTION
≠ BROKER
```

Prompt 17 introduces:

```text
CAPITAL ALLOCATION
INVESTMENT DECISION
TARGET POSITION
DECISION STATE
CAPITAL / RISK BUDGET
```

It must not redefine existing objects.

---

# 2. ARCHITECTURAL POSITION

The complete research-to-capital pipeline becomes:

```text
                         QUANT LAB
                            │
                    ┌───────▼───────┐
                    │ PIT DATA FABRIC│
                    └───────┬───────┘
                            │
             ┌──────────────▼──────────────┐
             │ FEATURES / FACTORS / ALPHAS  │
             └──────────────┬──────────────┘
                            │
                    MODELS / ADAPTIVE
                            │
                            ▼
                     META-ALPHA
                            │
                            ▼
                  PORTFOLIO CONSTRUCTION
                            │
                            ▼
                    RISK ENGINE
                            │
                            ▼
                  EXECUTION RESEARCH
                            │
                            ▼
                   RESEARCH VALIDATION
                            │
                            ▼
                    RESEARCH GATE
                            │
                            ▼
              KNOWLEDGE / EVIDENCE GRAPH
                            │
                            ▼
┌──────────────────────────────────────────────────────┐
│ PROMPT 17                                             │
│ CAPITAL ALLOCATION / INVESTMENT DECISION ENGINE       │
│                                                      │
│ expected return                                      │
│ risk budget                                          │
│ volatility target                                    │
│ factor exposure                                      │
│ concentration                                        │
│ liquidity                                            │
│ turnover                                             │
│ drawdown state                                       │
│ capital budget                                       │
│ confidence / evidence state                          │
│ optimization                                         │
│ abstention                                           │
│ deterministic decision                               │
└──────────────────────────┬───────────────────────────┘
                           │
                           ▼
                   TARGET PORTFOLIO
                           │
                           ▼
             PROMPT 18 — PAPER OMS
                           │
                           ▼
          PROMPT 19 — BROKER ABSTRACTION
                           │
                           ▼
             PROMPT 20 — ZERODHA
```

---

# 3. PACKAGE

Create:

```text
src/quantlab/capital/
```

Recommended structure:

```text
capital/
├── __init__.py
├── definitions.py
├── budgets.py
├── allocator.py
├── decision.py
├── constraints.py
├── sizing.py
├── volatility_target.py
├── kelly.py
├── concentration.py
├── turnover.py
├── liquidity.py
├── drawdown.py
├── exposure.py
├── optimizer.py
├── abstention.py
├── diagnostics.py
├── provenance.py
├── identity.py
├── validation.py
├── serialization.py
└── errors.py
```

`__init__.py` must remain thin.

Do not import:

```text
broker
zerodha
kite
openalgo
OMS
UI
Qt
```

into the capital package.

---

# 4. CORE DOMAIN OBJECTS

Implement strongly typed immutable domain objects.

At minimum:

## 4.1 CapitalPolicy

Defines available capital and capital-allocation rules.

Fields should include:

```text
policy_id
version
base_currency
starting_capital
available_capital
gross_leverage_limit
net_exposure_limit
cash_floor
max_position_weight
max_single_name_risk
max_turnover
target_volatility
volatility_lookback
risk_budget_method
kelly_fraction
kelly_cap
drawdown_limits
liquidity_policy
confidence_policy
constraint_policy
created_at
config_hash
```

No magic constants.

---

# 5. CAPITAL MUST HAVE EXPLICIT ACCOUNTING

Never silently assume:

```text
capital = portfolio value
```

Represent explicitly:

```text
equity
cash
reserved_cash
investable_capital
gross_exposure
net_exposure
margin_usage
available_margin
unrealized_pnl
realized_pnl
```

Prompt 17 may use a simulated research capital state.

It must not query a live broker.

Future broker values will arrive through a broker abstraction.

---

# 6. DECISION OBJECT

Create:

```text
InvestmentDecision
```

It must represent a complete deterministic decision at time T.

Minimum fields:

```text
decision_id
decision_time
snapshot_id
experiment_id
research_result_id
knowledge_snapshot_id

strategy_id
ensemble_id
portfolio_spec_id
risk_policy_id
capital_policy_id

decision_status

input_alpha_version
risk_model_version
covariance_version
regime_version
execution_model_version

expected_return
expected_risk
expected_volatility

gross_target
net_target

target_positions
target_weights

risk_contribution
factor_exposure
constraint_status

turnover_estimate
liquidity_status

confidence
evidence_status

abstention_reason

config_hash
decision_hash
created_at
```

Decision objects must be immutable after creation.

If anything changes:

> create a new decision.

Never mutate historical decisions.

---

# 7. DECISION STATUS

Use explicit states:

```text
REJECTED
ABSTAIN
RESEARCH_ONLY
ELIGIBLE
ALLOCATED
PAPER_READY
```

Do NOT create:

```text
LIVE_READY
LIVE_APPROVED
LIVE_ORDERED
```

in Prompt 17.

Those belong to later safety and execution architecture.

---

# 8. ALLOCATION PIPELINE

Implement exactly:

```text
RESEARCH INPUTS
      ↓
INPUT VALIDATION
      ↓
PIT SNAPSHOT FREEZE
      ↓
RESEARCH GATE CHECK
      ↓
EXPECTED-RETURN NORMALIZATION
      ↓
RISK ESTIMATION
      ↓
RISK BUDGET
      ↓
CAPITAL BUDGET
      ↓
POSITION-SIZING CANDIDATES
      ↓
LIQUIDITY FILTER
      ↓
CONSTRAINT ENGINE
      ↓
PORTFOLIO OPTIMIZATION
      ↓
VOLATILITY TARGETING
      ↓
TURNOVER CONTROL
      ↓
DRAWDOWN / CAPITAL STATE
      ↓
ABSTENTION CHECK
      ↓
TARGET PORTFOLIO
      ↓
DECISION RECORD
      ↓
KNOWLEDGE / LEDGER LINEAGE
```

No stage may use future information.

---

# 9. RESEARCH GATE INTEGRATION

Prompt 17 must consume Prompt 05 gate results.

It must never replace the research gate.

Required behavior:

```text
FAIL
→ allocation prohibited

WARN
→ allocation policy decides whether research-only allocation is permitted

RESEARCH_CANDIDATE
→ eligible for controlled allocation

PROMOTED_TO_PAPER
→ eligible for paper target generation
```

Because the existing gate does not authorize live trading, Prompt 17 must not introduce such a state.

Synthetic datasets:

```text
synthetic
→ cannot become production allocation
→ target may be generated only as research diagnostics
→ explicit synthetic warning
```

---

# 10. EXPECTED RETURN MODEL

Expected return must be explicitly defined.

Never infer:

```text
Sharpe = expected return
```

Represent:

```text
expected_return
expected_return_source
expected_return_horizon
expected_return_confidence
```

Possible sources:

```text
alpha
ensemble
model
adaptive_model
research_override
baseline
```

Research overrides must be recorded and cannot bypass gates.

---

# 11. RISK MODEL INTEGRATION

Reuse Prompt 08 risk infrastructure.

Do not build a second covariance implementation.

Inputs may include:

```text
idiosyncratic risk
factor risk
market beta
momentum exposure
volatility exposure
cross-sectional covariance
portfolio covariance
```

Portfolio variance:

```text
σ²_p = wᵀΣw
```

Portfolio volatility:

```text
σ_p = sqrt(wᵀΣw)
```

All covariance inputs must be PIT-valid.

Missing covariance:

```text
NOT_TESTED
```

not zero.

---

# 12. RISK BUDGETING

Implement explicit risk budgets.

Methods:

```text
equal_risk
inverse_volatility
risk_parity
factor_risk_budget
hierarchical_risk_budget
custom_budget
```

Risk contribution:

```text
RC_i = w_i * (Σw)_i / σ_p
```

Relative risk contribution:

```text
RRC_i = RC_i / σ_p
```

Record:

```text
absolute_risk_contribution
relative_risk_contribution
risk_budget
risk_budget_deviation
```

---

# 13. VOLATILITY TARGETING

Implement portfolio volatility targeting.

Example:

```text
target_vol = 15%
estimated_vol = 12%

gross_scaler = 15 / 12
```

But scaling must be bounded by:

```text
gross_leverage_limit
net_exposure_limit
capital_limit
liquidity_limit
position_limit
factor_limit
```

If target volatility cannot be achieved:

```text
TARGET_UNACHIEVABLE
```

Do not silently increase leverage.

---

# 14. KELLY POSITION SIZING

Implement Kelly only as a constrained research sizing method.

For simplified assumptions:

```text
f* = μ / σ²
```

For a binary payoff model:

```text
f* = (bp - q) / b
```

Implement:

```text
full_kelly
fractional_kelly
kelly_cap
```

Default should be conservative.

Example:

```text
kelly_fraction = 0.25
```

Kelly must never override:

- risk limits
- drawdown limits
- concentration limits
- liquidity limits
- factor limits
- capital limits
- turnover limits

If inputs are unreliable:

```text
KELLY_UNRELIABLE
```

and abstain or fall back according to explicit policy.

---

# 15. POSITION SIZING

Implement multiple sizing methods:

```text
equal_weight
score_weight
inverse_vol
risk_budget
vol_target
fractional_kelly
confidence_scaled
hybrid
```

Every sizing method must expose:

```text
method_id
parameters
input_versions
output_weights
diagnostics
```

No hidden sizing logic.

---

# 16. CONFIDENCE-AWARE ALLOCATION

Confidence is NOT probability of profit.

Represent:

```text
research_confidence
statistical_confidence
model_stability
execution_confidence
data_quality
evidence_strength
```

Produce a bounded:

```text
allocation_confidence
```

Do not allow confidence to override hard risk limits.

Low confidence may:

```text
reduce allocation
or
abstain
```

---

# 17. CONCENTRATION CONTROL

Implement:

```text
max_single_name_weight
max_top_5_weight
max_top_10_weight
Herfindahl-Hirschman Index
effective_number_of_positions
```

HHI:

```text
HHI = Σ w_i²
```

Effective number:

```text
N_eff = 1 / Σw_i²
```

Support:

```text
hard limits
soft penalties
diagnostic warnings
```

Hard limits must never be silently relaxed.

---

# 18. TURNOVER BUDGET

Reuse Prompt 07 convention:

```text
turnover = 0.5 × L1(new_weights - old_weights)
```

Support:

```text
max_turnover
turnover_penalty
minimum_trade_threshold
rebalance_band
```

Never use same-bar fills.

Prompt 17 creates targets only.

---

# 19. LIQUIDITY-AWARE CAPITAL ALLOCATION

Reuse Prompt 13 execution-research inputs.

Never invent ADV.

Inputs may include:

```text
PIT volume
trailing volume
participation limit
estimated notional capacity
execution cost estimate
```

If volume is unavailable:

```text
liquidity = UNKNOWN
```

Do not interpret unknown liquidity as infinite liquidity.

Allocation must be able to abstain because liquidity is unknown.

---

# 20. EXECUTION-COST-AWARE ALLOCATION

Use Prompt 13 execution research.

Estimate:

```text
expected_slippage
spread_cost
impact_cost
commission
total_execution_drag
```

Allocation may optimize:

```text
expected_return - expected_execution_cost
```

but must preserve gross and net metrics separately.

Never hide execution drag inside expected return.

---

# 21. FACTOR EXPOSURE CONSTRAINTS

Reuse Prompt 08.

Implement:

```text
max_beta
min_beta
max_factor_exposure
min_factor_exposure
factor_neutral
factor_budget
```

Portfolio factor exposure:

```text
B_p = Σ w_i B_i
```

Missing factor exposure:

```text
None / NOT_TESTED
```

Never silently substitute zero.

---

# 22. SECTOR CONSTRAINT INTERFACE

Prompt 08 may still have sector as NOT_TESTED.

Prompt 17 must support the future interface:

```text
max_sector_weight
min_sector_weight
sector_neutral
sector_risk_budget
```

If actual PIT sector data does not exist:

```text
sector_constraint = NOT_TESTED
```

Do not fabricate sector classifications.

---

# 23. MARKET-NEUTRAL MODES

Support:

```text
long_only
long_bias
dollar_neutral
beta_neutral
factor_neutral
long_short
```

Long-short constraints:

```text
gross exposure
net exposure
long exposure
short exposure
borrow availability
shorting eligibility
```

Unknown shortability:

```text
NOT_TESTED
```

Do not assume every security is shortable.

---

# 24. PORTFOLIO OPTIMIZATION

Build an optimizer around existing portfolio/risk abstractions.

Candidate objectives:

```text
maximize expected return
maximize expected utility
maximize return / risk
minimize variance
minimize tracking error
maximize risk-adjusted score
```

Example mean-variance objective:

```text
max_w:

μᵀw - λ wᵀΣw
```

Subject to explicit constraints.

Do not introduce an optimizer that silently modifies constraints.

---

# 25. INFEASIBILITY

Any hard-constraint conflict must raise a typed exception:

```text
InfeasibleCapitalAllocation
```

Include:

```text
violated_constraints
required_adjustment
current_candidate
feasibility_diagnostics
```

Never:

```text
relax constraint automatically
```

Never:

```text
clip silently
```

Never:

```text
fallback to arbitrary equal weight
```

unless the policy explicitly specifies a fallback.

---

# 26. DRAWDOWN-AWARE CAPITAL STATE

Implement deterministic capital states:

```text
NORMAL
CAUTION
DEFENSIVE
HALTED
```

Example policy:

```text
drawdown < 5%      → NORMAL
5–10%              → CAUTION
10–15%             → DEFENSIVE
>15%               → HALTED
```

These values must be configurable.

Do not hard-code them into the engine.

When halted:

```text
no new exposure
```

Existing positions are not automatically liquidated by Prompt 17.

Liquidation belongs to future OMS/risk execution architecture.

---

# 27. CAPITAL ALLOCATION STATES

Implement:

```text
FULL
REDUCED
DEFENSIVE
ABSTAIN
HALT
```

Capital multiplier:

```text
1.0
0.5
0.25
0.0
0.0
```

These must be policy-driven.

---

# 28. ABSTENTION ENGINE

Abstention is a first-class research decision.

Abstain when:

```text
research gate fails
PIT integrity fails
risk estimate unavailable
covariance invalid
liquidity unknown under strict policy
factor exposure unknown under strict policy
expected return unavailable
confidence below threshold
drawdown halt
constraint infeasible
execution drag overwhelms expected edge
data quality insufficient
model stability fails
```

Record exactly why.

Required:

```text
abstention_code
abstention_reason
abstention_stage
```

---

# 29. DECISION DETERMINISM

For identical:

```text
snapshot
research evidence
portfolio specification
risk model
capital policy
execution assumptions
```

the engine must produce:

```text
identical target weights
identical diagnostics
identical decision_hash
```

unless explicit stochastic behavior is configured.

If randomness is used:

```text
random_seed
algorithm
library_version
```

must be recorded.

---

# 30. DECISION HASH

Create canonical hashing.

Decision identity must include:

```text
snapshot_id
dataset_checksum
portfolio_spec
alpha identity
model identity
risk model identity
capital policy
constraints
execution assumptions
software version
```

Any material change creates a new decision identity.

---

# 31. KNOWLEDGE GRAPH INTEGRATION

Prompt 16 must become the scientific memory boundary.

Every decision should link:

```text
knowledge snapshot
hypothesis
evidence
research experiment
alpha
model
ensemble
portfolio
risk model
capital policy
execution assumptions
decision
```

Example:

```text
HYPOTHESIS
   ↓
EVIDENCE
   ↓
ALPHA
   ↓
MODEL
   ↓
ENSEMBLE
   ↓
PORTFOLIO
   ↓
RISK
   ↓
CAPITAL DECISION
```

The graph must preserve failed and rejected decisions.

---

# 32. LEDGER INTEGRATION

Prompt 17 must not create a second ledger.

Reuse the existing JSONL ledger.

Add:

```text
selection_stage = "capital_allocation"
```

Optional fields:

```text
decision_id
capital_policy_id
risk_budget_id
allocation_method
decision_status
abstention_code
capital_state
allocation_confidence
target_portfolio_hash
```

Existing ledger rows must remain backward compatible.

---

# 33. INTEGRITY CHECKS

Add dedicated integrity flags.

At minimum:

```text
future_capital_input
future_risk_input
future_expected_return
future_covariance
future_factor_exposure
future_liquidity
future_turnover_state
future_drawdown_state
future_constraint_parameter
future_position_reference
future_decision_state
capital_policy_mutation
decision_mutation
decision_hash_mismatch
allocation_lineage_break
hidden_constraint_relaxation
silent_fallback
unknown_liquidity_as_infinite
unknown_factor_as_zero
synthetic_capital_overpromotion
gate_bypass
abstention_suppression
future_portfolio_state
future_execution_cost
```

Rules:

```text
None → NOT_TESTED
direct leakage → FAIL
contradictory evidence → NOT automatically PASS
synthetic → WARN at best
```

---

# 34. NO LOOK-AHEAD

A decision at T may use only:

```text
available_time <= T
```

It may not use:

```text
T+1 return
future realized volatility
future covariance
future factor exposure
future liquidity
future portfolio performance
future drawdown
future execution outcome
future knowledge claims
```

Test this explicitly by appending future rows.

Historical decision must remain identical.

---

# 35. ADVERSARIAL TESTING

Create tests that intentionally inject:

```text
future return
future volume
future covariance
future factor data
future portfolio state
future execution cost
future drawdown
future parameter update
```

Every direct leak must fail.

---

# 36. SYNTHETIC DATA POLICY

Synthetic data remains:

```text
architecture diagnostic
```

Never:

```text
market evidence
```

Synthetic experiments must not reach:

```text
RESEARCH_CANDIDATE
PROMOTED_TO_PAPER
```

through Prompt 17.

---

# 37. CLI

Implement:

```bash
quantlab capital list
quantlab capital inspect <policy>
quantlab capital validate <policy>
quantlab capital allocate <portfolio>
quantlab capital decision <decision_id>
quantlab capital explain <decision_id>
quantlab capital constraints <decision_id>
quantlab capital risk <decision_id>
quantlab capital exposure <decision_id>
quantlab capital sizing <decision_id>
quantlab capital turnover <decision_id>
quantlab capital liquidity <decision_id>
quantlab capital drawdown <decision_id>
quantlab capital compare <decision_a> <decision_b>
quantlab capital lineage <decision_id>
quantlab capital abstentions
quantlab capital report <decision_id>
```

Research aliases:

```bash
quantlab research capital
quantlab research allocation
quantlab research decision
quantlab research risk-budget
quantlab research sizing
quantlab research capital-efficiency
quantlab research allocation-stability
```

Do not break existing commands.

---

# 38. APPLICATION SERVICE

Extend:

```text
quantlab.app
```

with read-only/query and job services.

Example:

```text
CapitalAllocationService
DecisionQueryService
CapitalDiagnosticsService
```

The application layer may orchestrate calculations.

The UI must not perform them.

---

# 39. DESKTOP — CAPITAL LAB

Add:

```text
Capital Lab
```

Navigation:

```text
Dashboard
Market
Research
Features
Alpha
Portfolio
Risk
Execution
Capital
Backtest
Validation
Experiments
Knowledge
System
Logs
```

Capital Lab should display:

```text
capital state
investable capital
target volatility
gross exposure
net exposure
risk budget
factor exposure
top positions
concentration
turnover
liquidity
execution drag
constraint status
decision status
abstention reason
decision lineage
```

The UI must:

- never calculate allocations
- never query Parquet directly
- never query DuckDB directly
- never import brokers
- never modify decisions
- never write ledger rows directly

It is a client of `quantlab.app`.

---

# 40. EXPLAINABILITY

Every decision must be explainable.

Implement:

```text
Why was this security allocated?
Why this weight?
Why was another security excluded?
Which constraint bound?
Which risk budget bound?
Which evidence supported the allocation?
Which evidence weakened it?
What would change the decision?
```

Produce structured explanations.

Example:

```text
ALLOCATION
AAPL-like synthetic security
target weight: 8.2%

Drivers:
+ momentum alpha
+ positive ensemble score
+ low residual volatility

Constraints:
max position = 10%
factor exposure = within limit
turnover = within budget

Binding constraint:
none

Confidence:
0.71

Status:
RESEARCH_ONLY
```

Never fabricate explanations.

---

# 41. ALLOCATION ATTRIBUTION

Decompose target allocation into:

```text
alpha contribution
risk contribution
factor contribution
confidence adjustment
liquidity adjustment
turnover adjustment
capital-state adjustment
constraint adjustment
execution-cost adjustment
```

The final weight must be reproducible from these transformations.

---

# 42. MARGINAL RISK

Implement:

```text
MRC_i = (Σw)_i / σ_p
```

and:

```text
RC_i = w_i × MRC_i
```

Provide:

```text
marginal volatility
marginal variance
risk contribution
percentage contribution
```

---

# 43. EXPECTED SHORTFALL INTERFACE

Provide an extensible interface for:

```text
VaR
Expected Shortfall
```

Do not pretend a simplistic historical estimate is institutional-grade if the sample is insufficient.

Mark:

```text
ESTIMATE
NOT_TESTED
```

as appropriate.

Do not replace the existing covariance engine.

---

# 44. STRESS TESTING

Reuse Prompt 08 stress infrastructure.

Support:

```text
market shock
volatility shock
correlation shock
factor shock
liquidity shock
execution-cost shock
drawdown shock
```

Stress output must be:

```text
scenario
portfolio loss estimate
risk impact
constraint breach
capital-state transition
```

Stress is:

> scenario analysis, not a forecast.

---

# 45. ALLOCATION STABILITY

Implement sensitivity to:

```text
alpha perturbation
covariance perturbation
expected-return perturbation
cost perturbation
risk-target perturbation
constraint perturbation
capital perturbation
```

Measure:

```text
weight stability
rank stability
turnover sensitivity
risk sensitivity
decision-state sensitivity
```

A fragile allocation should be clearly labeled.

---

# 46. CAPITAL EFFICIENCY

Calculate:

```text
return / capital
return / risk
return / turnover
return / execution cost
risk-adjusted capital efficiency
```

Do not use future realized returns as allocation inputs.

These metrics may be used for research evaluation.

---

# 47. CAPITAL UTILIZATION

Track:

```text
cash utilization
gross utilization
risk utilization
turnover utilization
liquidity utilization
factor budget utilization
```

Example:

```text
risk budget utilization = current risk / permitted risk
```

---

# 48. NO AUTOMATIC LEVERAGE ESCALATION

The engine must never respond to low volatility by automatically increasing leverage beyond the configured maximum.

Volatility targeting is subordinate to:

```text
hard leverage limit
hard risk limit
capital policy
drawdown state
liquidity
```

---

# 49. SAFETY BOUNDARY

Prompt 17 must contain an explicit assertion:

```python
assert live_trading is False
```

or equivalent fail-closed enforcement.

If an external configuration attempts:

```text
LIVE_TRADING=true
```

Prompt 17 must refuse to initialize any production allocation path.

Do not merely display a warning.

Fail closed.

---

# 50. BROKER ISOLATION

The following must remain absent from Prompt 17 imports:

```python
kiteconnect
zerodha
openalgo
broker
```

Broker integration begins only in later prompts.

The output of Prompt 17 is:

```text
TargetPortfolio
InvestmentDecision
```

NOT:

```text
Order
OrderIntent
BrokerOrder
```

---

# 51. TARGET PORTFOLIO

Create an immutable:

```text
TargetPortfolio
```

with:

```text
portfolio_id
decision_id
timestamp
weights
notional_targets
gross_exposure
net_exposure
cash_target
risk_target
turnover_estimate
constraint_state
portfolio_hash
```

No order semantics.

---

# 52. FUTURE OMS CONTRACT

Prompt 17 should expose a clean future boundary:

```text
TargetPortfolio
       ↓
Future Prompt 18
       ↓
Order Planning
```

Prompt 17 must not construct orders.

---

# 53. REPRODUCIBILITY

Every allocation must be reproducible using:

```text
dataset checksum
snapshot id
feature versions
alpha versions
model versions
ensemble versions
portfolio specification
risk model version
capital policy
execution assumptions
software version
configuration hash
```

Store all identifiers.

---

# 54. RESEARCH EXPERIMENT INTEGRATION

Prompt 14 orchestration must be able to run capital-allocation experiments.

Examples:

```text
compare sizing methods
compare risk budgets
compare Kelly fractions
compare volatility targets
compare concentration limits
compare turnover budgets
compare execution assumptions
```

Every candidate must be recorded.

Do not hide failed candidates.

---

# 55. MULTIPLE TESTING

Prompt 17 must not create another FDR engine.

If comparing allocation families:

```text
reuse Prompt 14 multiple-testing infrastructure
```

The system must record:

```text
tested_count
family_id
selection_policy
selection_stage
```

Avoid:

```text
choose maximum Sharpe after search
```

without explicit selection accounting.

---

# 56. KNOWLEDGE MEMORY

Record:

```text
successful allocations
failed allocations
infeasible portfolios
abstentions
fragile allocations
constraint failures
capacity failures
risk failures
```

A failed capital policy is useful research knowledge.

Never delete it.

---

# 57. DOCUMENTATION

Create:

```text
docs/architecture/CAPITAL_ALLOCATION_ENGINE.md
docs/architecture/INVESTMENT_DECISION_ENGINE.md
docs/architecture/CAPITAL_RISK_BUDGETING.md
docs/research/CAPITAL_ALLOCATION_RESEARCH.md
docs/research/POSITION_SIZING.md
docs/research/KELLY_SIZING.md
docs/research/ALLOCATION_STABILITY.md
docs/decisions/ADR-031-capital-allocation-decision-engine.md
```

Update:

```text
README.md
BACKLOG.md
LOCAL_RUN.md
architecture map
version metadata
```

---

# 58. ADR-031

Create an ADR documenting:

1. Why capital allocation is separate from portfolio construction.
2. Why target portfolios are separate from orders.
3. Why broker integration is prohibited.
4. Why capital accounting is explicit.
5. Why risk budgets are first-class.
6. Why Kelly is constrained.
7. Why abstention is a valid decision.
8. Why hard constraints cannot be silently relaxed.
9. Why PIT is mandatory.
10. Why decisions are immutable.
11. Why decision hashes are required.
12. Why synthetic data cannot promote.
13. Why Prompt 05 remains the only research gate.
14. Why Prompt 18 owns order lifecycle.

---

# 59. TEST SUITE

Create:

```text
tests/capital/
├── test_definitions.py
├── test_budget.py
├── test_sizing.py
├── test_kelly.py
├── test_vol_target.py
├── test_constraints.py
├── test_optimizer.py
├── test_turnover.py
├── test_liquidity.py
├── test_drawdown.py
├── test_decision.py
├── test_determinism.py
├── test_provenance.py
├── test_integrity.py
├── test_abstention.py
├── test_stress.py
├── test_stability.py
└── test_end_to_end.py
```

---

# 60. MANDATORY TEST CASES

Test:

### Capital

- available capital
- cash floor
- capital reservation
- leverage

### Risk

- covariance
- portfolio volatility
- marginal risk
- risk contribution
- risk budgets

### Sizing

- equal weight
- inverse vol
- score weight
- fractional Kelly
- volatility target

### Constraints

- position limit
- factor limit
- beta limit
- turnover limit
- gross exposure
- net exposure
- concentration

### Failure

- infeasible portfolio
- missing covariance
- missing liquidity
- invalid expected return
- gate failure
- drawdown halt
- capital insufficiency

### Integrity

- future data
- future covariance
- future liquidity
- future drawdown
- future portfolio state
- hidden relaxation
- silent fallback
- decision mutation

### Reproducibility

Run identical input twice.

Require:

```text
same target weights
same diagnostics
same decision hash
```

---

# 61. ADVERSARIAL REGRESSION TEST

Implement the following critical test:

```text
RUN DECISION AT T
        ↓
APPEND DATA FROM T+1 → T+N
        ↓
RUN DECISION AGAIN AT T
```

Expected:

```text
decision_before == decision_after
```

including:

```text
weights
risk
constraints
diagnostics
decision_hash
```

If not:

```text
FAIL
```

This test is mandatory.

---

# 62. END-TO-END TEST

Required:

```text
PIT snapshot
   ↓
validated research result
   ↓
alpha / ensemble
   ↓
portfolio
   ↓
risk model
   ↓
execution assumptions
   ↓
capital policy
   ↓
allocation
   ↓
target portfolio
   ↓
decision
   ↓
ledger
   ↓
knowledge graph
```

Verify complete lineage.

---

# 63. VERSION

Upon successful implementation:

```python
__version__ = "1.7.0"
```

Do not modify prior version semantics.

---

# 64. QUALITY GATES

Cursor must not declare Prompt 17 complete merely because code compiles.

Required:

```text
ruff clean
mypy --strict clean
full pytest passing
capital tests passing
integrity tests passing
UI offscreen passing
architecture regression passing
```

The existing Prompt 01–16 tests must remain passing.

---

# 65. REQUIRED REPORT

At completion provide:

```text
PROMPT 17 STATUS
VERSION
FILES CREATED
FILES MODIFIED
ARCHITECTURAL CHANGES
CLI COMMANDS
DESKTOP CHANGES
TEST COUNT
RUFF
MYPY
PIT TEST RESULTS
INTEGRITY RESULTS
DETERMINISM RESULTS
KNOWLEDGE-LINEAGE RESULTS
LIVE_TRADING STATUS
BROKER IMPORT AUDIT
KNOWN NOT_TESTED
KNOWN LIMITATIONS
NEXT RECOMMENDED PROMPT
```

Do not report synthetic performance as market evidence.

---

# 66. DEFINITION OF DONE

Prompt 17 is complete only when:

- [ ] Capital policy exists.
- [ ] Capital accounting is explicit.
- [ ] Risk budgets exist.
- [ ] Multiple sizing methods exist.
- [ ] Fractional Kelly is constrained.
- [ ] Volatility targeting exists.
- [ ] Concentration controls exist.
- [ ] Turnover budgets exist.
- [ ] Liquidity-aware allocation exists.
- [ ] Factor exposure constraints integrate with Prompt 08.
- [ ] Execution-cost assumptions integrate with Prompt 13.
- [ ] Research gate integrates with Prompt 05.
- [ ] Knowledge lineage integrates with Prompt 16.
- [ ] Existing portfolio construction is reused, not duplicated.
- [ ] Existing covariance is reused.
- [ ] Existing backtester is reused for research evaluation.
- [ ] Hard constraints cannot silently relax.
- [ ] Abstention is first-class.
- [ ] Decisions are immutable.
- [ ] Decision hashes are deterministic.
- [ ] Future-data mutation tests pass.
- [ ] Synthetic data cannot promote.
- [ ] Broker imports are absent.
- [ ] `LIVE_TRADING=false`.
- [ ] No order objects are produced.
- [ ] Desktop Capital Lab is query-only.
- [ ] CLI works.
- [ ] Documentation exists.
- [ ] ADR-031 exists.
- [ ] Existing Prompts 01–16 regression suite passes.

---

# 67. FINAL ARCHITECTURAL CONTRACT

The most important boundary is:

```text
                    RESEARCH
                       │
                       ▼
                RESEARCH GATE
                       │
                       ▼
              CAPITAL ALLOCATION
                       │
                       ▼
              INVESTMENT DECISION
                       │
                       ▼
                TARGET PORTFOLIO
                       │
                       │
             ===== BOUNDARY =====
                       │
                       ▼
                  PAPER OMS
                       │
                       ▼
               BROKER ABSTRACTION
                       │
                       ▼
                    ZERODHA
```

Prompt 17 owns everything **above the boundary**.

Prompt 18 will own the next layer.

Therefore:

> **Prompt 17 may allocate capital. It may generate target positions. It may reject or abstain. It may explain every decision. It may not submit, modify, cancel, or route an order.**

The architecture must remain fail-closed.

---

# 68. FINAL DIRECTIVE TO CURSOR

Do not treat this prompt as a request for a demonstration.

Treat it as an **institutional quantitative-system engineering milestone**.

First inspect the existing QUANT LAB 1.6.0 repository and Prompts 01–16.

Before coding:

1. Map existing modules.
2. Identify reusable abstractions.
3. Identify duplication risks.
4. Inspect existing portfolio, risk, execution-research, orchestration, knowledge and ledger contracts.
5. Produce an implementation plan.
6. Implement incrementally.
7. Add tests before declaring components complete.
8. Run adversarial PIT tests.
9. Run the entire regression suite.
10. Audit imports for broker leakage.
11. Audit `LIVE_TRADING`.
12. Verify deterministic decision hashing.
13. Verify knowledge and ledger lineage.
14. Update architecture documentation.
15. Only then declare Prompt 17 complete.

Never rewrite stable Prompt 01–16 components merely to make Prompt 17 easier.

**Reuse. Extend. Compose. Do not fork the architecture.**

The objective is not to create another trading strategy.

The objective is to create a deterministic, auditable, research-grounded **capital decision system** capable of eventually sitting safely upstream of a professional OMS and broker integration.

**END OF PROMPT 17**
