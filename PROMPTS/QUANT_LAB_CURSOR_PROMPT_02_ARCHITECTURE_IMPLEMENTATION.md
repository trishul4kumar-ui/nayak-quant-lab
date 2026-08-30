# QUANT LAB — CURSOR PROMPT 02
## Architecture Integration, Quantitative Research Core & Engineering Implementation Directive
### Version 0.2 — Continuation Prompt
### Date: 2026-08-30

---

> **EXECUTION MODE: PRINCIPAL ARCHITECT + QUANT RESEARCH ENGINEER**
>
> The first QUANT LAB prompt has already been given to you and you are currently executing it.
>
> **DO NOT restart the project. DO NOT discard existing work. DO NOT replace the architecture already created.**
>
> This is the **second-stage architecture and implementation directive**.
>
> Your task now is to take the repository intelligence gathered from the first prompt and integrate it with the previously defined QUANT LAB architecture described below.
>
> The open-source repositories are REFERENCES.
>
> **QUANT LAB's architecture is the destination.**

---

# 0. PRIMARY OBJECTIVE

Build **QUANT LAB** as a local-first, research-first quantitative trading laboratory for the Indian financial markets.

The long-term system must combine:

```text
Mathematics
+
Statistics
+
Econometrics
+
Signal Processing
+
Time-Series Analysis
+
Optimization
+
Machine Learning
+
Artificial Intelligence
+
Market Microstructure
+
Portfolio Theory
+
Risk Engineering
+
Algorithmic Execution
```

The objective is NOT:

```text
LLM → stock prediction → BUY
```

The objective is:

```text
OBSERVE
   ↓
REPRESENT
   ↓
MEASURE
   ↓
FORM HYPOTHESIS
   ↓
EXPERIMENT
   ↓
FALSIFY
   ↓
DISCOVER ALPHA
   ↓
VALIDATE
   ↓
CONSTRUCT PORTFOLIO
   ↓
CONTROL RISK
   ↓
EXECUTE
   ↓
MEASURE OUTCOME
   ↓
LEARN
```

QUANT LAB must behave more like a **scientific laboratory + quantitative research platform + execution system** than a conventional retail trading application.

---

# 1. ARCHITECTURAL AUTHORITY

The previously developed QUANT LAB architecture is the baseline.

The repository research from Prompt 01 must be used to:

- improve implementation quality;
- identify missing capabilities;
- identify better abstractions;
- identify failure modes;
- compare architectural alternatives;
- avoid reinventing mature infrastructure unnecessarily.

It must NOT automatically redefine QUANT LAB.

For every major architectural deviation:

1. identify the reason;
2. compare alternatives;
3. document the decision;
4. create/update an ADR;
5. implement only after the decision is justified.

Use this hierarchy:

```text
QUANT LAB DESIGN PRINCIPLES
        ↓
QUANT LAB ARCHITECTURE
        ↓
ARCHITECTURE DECISION RECORDS
        ↓
REFERENCE REPOSITORY INSIGHTS
        ↓
IMPLEMENTATION
```

NOT:

```text
GitHub repository
      ↓
copy architecture
      ↓
rename it QUANT LAB
```

---

# 2. THE CORE PHILOSOPHY

QUANT LAB should be inspired by the **research philosophy of systematic quantitative investing**, including the general methodology associated with Jim Simons/Renaissance Technologies:

```text
Find measurable structure
        ↓
Represent it mathematically
        ↓
Generate hypotheses
        ↓
Test statistically
        ↓
Reject weak hypotheses
        ↓
Search for robust signals
        ↓
Combine weak independent edges
        ↓
Control risk
        ↓
Execute efficiently
```

Do NOT interpret this as a requirement to reproduce Renaissance Technologies' proprietary methods.

We are building our own system.

The important principles are:

- scientific experimentation;
- statistical rigor;
- large-scale hypothesis testing;
- signal combination;
- low reliance on human intuition alone;
- strong out-of-sample validation;
- disciplined execution;
- continuous research.

---

# 3. QUANT LAB SYSTEM VISION

Target architecture:

```text
                              ┌───────────────────────┐
                              │       QUANT LAB       │
                              │ Quant Research &      │
                              │ Trading Laboratory    │
                              └───────────┬───────────┘
                                          │
             ┌────────────────────────────┼────────────────────────────┐
             │                            │                            │
             ▼                            ▼                            ▼
       DATA FABRIC                 QUANT/MATH CORE                 AI CORE
             │                            │                            │
             ▼                            ▼                            ▼
       MARKET STATE              FEATURE / FACTOR ENGINE       RESEARCH AGENTS
             │                            │                            │
             └────────────────────────────┼────────────────────────────┘
                                          ▼
                                  ALPHA DISCOVERY
                                          │
                                          ▼
                                   SIGNAL GENOME
                                          │
                                          ▼
                                  MODEL FACTORY
                                          │
                                          ▼
                              RESEARCH INTEGRITY ENGINE
                                          │
                                          ▼
                                PORTFOLIO ENGINE
                                          │
                                          ▼
                                  RISK FIREWALL
                                          │
                                          ▼
                                EXECUTION ENGINE
                                          │
                                          ▼
                              BROKER ABSTRACTION LAYER
                                          │
                                ┌─────────┴─────────┐
                                ▼                   ▼
                             OpenAlgo           Zerodha
```

---

# 4. THE MOST IMPORTANT ARCHITECTURAL OBJECT: MARKET STATE

QUANT LAB must NOT force every strategy to independently interpret raw OHLCV.

Create a canonical **MarketState** representation.

Conceptually:

```text
                         MARKET STATE
                              │
        ┌─────────────────────┼──────────────────────┐
        │                     │                      │
        ▼                     ▼                      ▼
   PRICE STATE           VOLATILITY STATE       LIQUIDITY STATE
        │                     │                      │
        ▼                     ▼                      ▼
   TREND STATE             REGIME STATE          FLOW STATE
        │                     │                      │
        └─────────────────────┼──────────────────────┘
                              ▼
                     MARKET REPRESENTATION
```

MarketState should eventually be able to represent:

```text
Price
Returns
Volume
Volatility
Liquidity
Spread
Order-book information
Momentum
Mean reversion
Correlation
Cross-sectional relationships
Market breadth
Sector structure
Factor exposures
Regime probabilities
Macro state
Sentiment
News/event state
Options state
Futures state
Market microstructure
```

Do not implement everything immediately.

First establish the abstraction and interfaces.

---

# 5. SIGNAL GENOME

Create a first-class representation for an alpha/signal.

The purpose is to allow QUANT LAB to eventually:

```text
GENERATE
MUTATE
COMBINE
TEST
FALSIFY
RANK
CLUSTER
PROMOTE
RETIRE
```

candidate signals.

Conceptual model:

```text
SignalGenome
│
├── Inputs
├── Data dependencies
├── Transformations
├── Mathematical operators
├── Features
├── Factors
├── Time horizon
├── Prediction horizon
├── Regime dependency
├── Signal direction
├── Entry logic
├── Exit logic
├── Position sizing
├── Neutralization
├── Constraints
├── Expected holding period
└── Provenance
```

Example conceptual expression:

```text
Signal =
    rank(
        zscore(
            momentum_20
            -
            volatility_adjustment
            +
            liquidity_factor
        )
    )
```

The system should eventually be able to represent such expressions as structured objects/ASTs rather than opaque strings.

Do not build a genetic algorithm immediately.

First build:

```text
Signal schema
+
expression representation
+
evaluation interface
+
metadata
+
versioning
```

---

# 6. ALPHA FACTORY

The Alpha Factory is a core QUANT LAB subsystem.

Target:

```text
Hypothesis
    ↓
Signal Genome
    ↓
Feature dependencies
    ↓
Historical evaluation
    ↓
Statistical test
    ↓
Robustness tests
    ↓
Cost-adjusted backtest
    ↓
Cross-validation
    ↓
Walk-forward
    ↓
Regime analysis
    ↓
Alpha score
    ↓
Promotion / rejection
```

An Alpha must have explicit metadata:

```text
alpha_id
name
hypothesis
universe
data_dependencies
features
signal_definition
prediction_horizon
holding_period
expected_direction
neutralization
constraints
validation_protocol
research_status
version
provenance
```

---

# 7. RESEARCH HYPOTHESIS ENGINE

Create a formal research object:

```text
ResearchHypothesis
```

Minimum conceptual fields:

```text
Hypothesis ID
Title
Statement
Economic intuition
Mathematical formulation
Expected effect
Universe
Time horizon
Required data
Potential confounders
Null hypothesis
Alternative hypothesis
Experiment design
Acceptance criteria
Rejection criteria
Researcher/agent
Timestamp
Version
```

The AI system may propose hypotheses.

The quant engine must test them.

---

# 8. SCIENTIFIC FALSIFICATION

QUANT LAB should not be optimized for finding reasons why a strategy works.

It must actively search for reasons why it does NOT work.

Every serious experiment should ask:

```text
Does the effect survive different periods?
Does it survive different universes?
Does it survive transaction costs?
Does it survive slippage?
Does it survive reasonable parameter changes?
Does it survive different market regimes?
Does it survive alternative formulations?
Does it survive removal of suspicious features?
Does it survive walk-forward validation?
Does it survive out-of-sample testing?
```

Build the architecture so a future **Research Critic / Red-Team Agent** can perform these checks.

---

# 9. RESEARCH INTEGRITY ENGINE

This is a mandatory subsystem.

Detect:

```text
Look-ahead bias
Survivorship bias
Selection bias
Data leakage
Feature leakage
Target leakage
Timestamp leakage
Corporate-action leakage
Universe leakage
Train/test contamination
Parameter overfitting
Multiple-hypothesis problems
Data snooping
Regime overfitting
Liquidity overestimation
Slippage underestimation
Transaction-cost underestimation
Capacity overestimation
Execution-latency assumptions
```

Every backtest/research run must report:

```text
PASS
WARN
FAIL
NOT_TESTED
```

for relevant integrity checks.

---

# 10. POINT-IN-TIME DATA

This is mandatory for serious historical research.

Maintain distinct temporal concepts:

```text
event_time
effective_time
available_time
ingestion_time
```

Example:

```text
Company announces earnings
        ↓
event_time

Accounting period represented
        ↓
effective_time

Information becomes available to market
        ↓
available_time

QUANT LAB receives/stores it
        ↓
ingestion_time
```

Historical models must never use information before `available_time`.

---

# 11. DATA PROVENANCE

Every research result must be able to answer:

```text
Where did this data come from?
Which provider?
Which dataset version?
When was it ingested?
What transformations occurred?
Which features were derived?
Which model consumed it?
```

Create lineage objects.

Conceptual:

```text
Raw Data
   ↓
Normalized Data
   ↓
Validated Data
   ↓
Dataset Version
   ↓
Feature Version
   ↓
Model Version
   ↓
Signal Version
   ↓
Backtest
   ↓
Strategy
```

---

# 12. EXPERIMENT LEDGER

Create a permanent experiment registry.

Each experiment must store:

```text
experiment_id
hypothesis_id
dataset_version
universe
feature_versions
label_definition
model_version
hyperparameters
random_seed
train_period
validation_period
test_period
cost_model
slippage_model
latency_model
execution assumptions
code commit
environment
metrics
risk metrics
artifacts
research conclusion
integrity checks
timestamp
```

The experiment must be reproducible.

---

# 13. MODEL FACTORY

Models are research artifacts.

Separate:

```text
Model
ModelVersion
TrainingRun
ValidationRun
ModelArtifact
```

Model lifecycle:

```text
CREATED
   ↓
TRAINED
   ↓
VALIDATED
   ↓
BACKTESTED
   ↓
STRESS_TESTED
   ↓
RESEARCH_APPROVED
   ↓
PAPER_APPROVED
   ↓
LIVE_APPROVED
   ↓
ACTIVE
   ↓
RETIRED
```

A profitable backtest must NOT automatically make a model production eligible.

---

# 14. MODEL TYPES

Build interfaces capable of supporting:

```text
Linear models
Tree models
Gradient boosting
Neural networks
Time-series models
State-space models
Bayesian models
Factor models
Ensembles
Online learning
```

Future research areas:

```text
Kalman filtering
HMM/regime models
Cointegration
PCA/ICA
Clustering
Graph methods
Bayesian inference
Robust optimization
Symbolic regression
Information theory
Reinforcement learning
```

Do not implement every model now.

Build extensible interfaces.

---

# 15. MATHEMATICAL CORE

Create a clean mathematical layer independent from broker/API/UI code.

Initial areas:

```text
Statistics
Probability
Linear Algebra
Optimization
Time Series
Signal Processing
Econometrics
Information Theory
Numerical Methods
Portfolio Mathematics
Risk Mathematics
```

Potential initial primitives:

```text
returns
log_returns
rolling statistics
z-score
correlation
covariance
rank transforms
winsorization
normalization
PCA
regression
rolling regression
drawdown
volatility
Sharpe
Sortino
beta
factor exposure
```

Keep mathematical functions deterministic and heavily tested.

---

# 16. MARKET MICROSTRUCTURE LAYER

Do not treat the market as an abstract price series forever.

Create interfaces capable of representing:

```text
Bid
Ask
Spread
Depth
Order Book
Trade Flow
Volume Imbalance
Order Imbalance
Liquidity
Market Impact
Queue Position
Execution Latency
```

This will support future intraday and execution research.

---

# 17. PORTFOLIO ENGINE

Maintain a strict separation:

```text
Signal
    ≠
Forecast
    ≠
Target Position
    ≠
Order
    ≠
Execution
```

Correct pipeline:

```text
Forecast / Signal
       ↓
Signal Transformation
       ↓
Portfolio Construction
       ↓
Target Positions
       ↓
Risk Adjustment
       ↓
Execution Planning
       ↓
Orders
       ↓
Fills
       ↓
Portfolio State
```

---

# 18. PORTFOLIO OPTIMIZATION

The architecture should support:

```text
Equal weight
Risk parity
Mean-variance
Minimum variance
Maximum diversification
Factor constrained optimization
Volatility targeting
CVaR optimization
Robust optimization
Black-Litterman-style approaches
Custom mathematical objectives
```

Do not implement all now.

Create a portfolio optimizer interface.

---

# 19. RISK ENGINE / CAPITAL FIREWALL

This is one of the highest-priority subsystems.

No:

```text
AI agent
strategy
notebook
API
UI
research script
```

may bypass the risk engine for live orders.

Architecture:

```text
TRADE PROPOSAL
      ↓
Instrument validation
      ↓
Account validation
      ↓
Position limit
      ↓
Order size limit
      ↓
Capital limit
      ↓
Portfolio exposure
      ↓
Sector/factor exposure
      ↓
Liquidity
      ↓
Volatility
      ↓
Drawdown state
      ↓
Daily loss
      ↓
Risk concentration
      ↓
Broker constraints
      ↓
Market state
      ↓
RISK DECISION
      ↓
APPROVE / MODIFY / REJECT
```

---

# 20. RISK STATES

Create explicit states:

```text
NORMAL
CAUTION
RESTRICTED
HALT
EMERGENCY
```

Example:

```text
NORMAL
→ normal operation

CAUTION
→ reduce risk / tighter limits

RESTRICTED
→ new exposure heavily constrained

HALT
→ no new orders

EMERGENCY
→ protective procedures only
```

Do not hardcode arbitrary values yet.

Make limits configurable.

---

# 21. EXECUTION ENGINE

Execution is independent of strategy.

Implement:

```text
OrderManager
ExecutionEngine
ExecutionPlanner
OrderRouter
ReconciliationEngine
BrokerGateway
```

Order lifecycle:

```text
CREATED
 ↓
VALIDATING
 ↓
RISK_PENDING
 ↓
APPROVED
 ↓
SUBMITTED
 ↓
ACKNOWLEDGED
 ↓
PARTIALLY_FILLED
 ↓
FILLED
```

Alternative terminal states:

```text
REJECTED
CANCELLED
FAILED
UNKNOWN
```

Never assume success merely because an API request returned HTTP 200.

---

# 22. RECONCILIATION ENGINE

This is mandatory before live deployment.

Continuously reconcile:

```text
QUANT LAB state
        vs
BROKER state
```

Compare:

```text
positions
orders
fills
cash
margin
open orders
average prices
quantities
```

If state becomes uncertain:

```text
STOP NEW LIVE ORDERS
```

until reconciliation is resolved.

---

# 23. BROKER ABSTRACTION

Define:

```python
class BrokerGateway(Protocol):
    ...
```

Broker-specific implementations must live behind this interface.

Target architecture:

```text
Strategy
   ↓
Portfolio
   ↓
Risk
   ↓
Execution
   ↓
BrokerGateway
   ├── PaperBroker
   ├── OpenAlgoBroker
   └── ZerodhaBroker
```

No strategy should import the Zerodha SDK directly.

---

# 24. ZERODHA

The intended eventual live path:

```text
QUANT LAB
   ↓
Risk Firewall
   ↓
Execution Engine
   ↓
Broker Gateway
   ↓
OpenAlgo / Zerodha adapter
   ↓
Zerodha
```

Live trading must be disabled by default.

Use:

```text
LIVE_TRADING=false
```

until explicit promotion.

---

# 25. EXECUTION SIMULATION

The backtester must eventually simulate:

```text
transaction costs
brokerage
exchange charges
taxes/fees where applicable
slippage
latency
partial fills
liquidity
market impact
order type
execution algorithm
```

Do not allow unrealistic zero-cost backtests to become the default definition of strategy performance.

---

# 26. BACKTEST ENGINE

Separate:

```text
Market Simulation
Strategy Runtime
Portfolio Accounting
Execution Simulation
Analytics
```

Architecture:

```text
Historical Market Events
        ↓
Strategy Runtime
        ↓
Signal
        ↓
Portfolio
        ↓
Risk
        ↓
Simulated Execution
        ↓
Fills
        ↓
Portfolio State
        ↓
Performance
```

The same strategy interface should eventually support:

```text
BACKTEST
PAPER
SHADOW
LIVE
```

---

# 27. RESEARCH → PAPER → LIVE PROMOTION

Mandatory lifecycle:

```text
RESEARCH
   ↓
BACKTEST
   ↓
ROBUSTNESS TEST
   ↓
PAPER
   ↓
SHADOW
   ↓
LIVE
```

Never:

```text
BACKTEST
   ↓
LIVE
```

automatically.

---

# 28. AI ARCHITECTURE

AI should operate as a controlled research layer.

Target agents:

```text
ResearchAgent
DataAnalystAgent
FeatureResearchAgent
AlphaDiscoveryAgent
StatisticalAnalystAgent
ModelAnalystAgent
ResearchCriticAgent
BullResearcher
BearResearcher
RiskReviewer
PortfolioAnalyst
ExecutionReviewer
PerformanceAnalyst
```

These roles may eventually be orchestrated as a multi-agent system.

But the deterministic quant core remains authoritative.

---

# 29. AI PERMISSION MODEL

Define explicit capabilities:

```text
READ_MARKET_DATA
READ_RESEARCH
CREATE_HYPOTHESIS
CREATE_FEATURE
CREATE_SIGNAL
RUN_EXPERIMENT
RUN_BACKTEST
CREATE_MODEL
REQUEST_PAPER_ORDER
REQUEST_LIVE_ORDER
```

Potential permissions:

```text
AI may:
✓ read
✓ analyze
✓ propose
✓ experiment
✓ critique
✓ simulate

AI may NOT:
✗ bypass risk
✗ alter risk limits
✗ directly place unrestricted live orders
✗ change broker credentials
✗ modify production models without approval
```

---

# 30. AI RESEARCH LOOP

Target:

```text
Market observation
      ↓
AI detects anomaly/pattern
      ↓
Hypothesis generated
      ↓
Quant formalization
      ↓
Feature construction
      ↓
Experiment
      ↓
Statistical evaluation
      ↓
Red-team critique
      ↓
Backtest
      ↓
Robustness
      ↓
Research report
      ↓
Promotion decision
```

The AI should generate **testable hypotheses**, not persuasive narratives.

---

# 31. AI RESEARCH MEMORY

Create a research memory architecture capable of storing:

```text
Hypotheses
Experiments
Rejected hypotheses
Successful factors
Failed factors
Research papers
Methodologies
Model results
Market regimes
Known failure modes
Strategy genealogy
```

Especially store rejected ideas.

A research system that forgets failed experiments will repeatedly rediscover the same false signals.

---

# 32. KNOWLEDGE GRAPH / PROVENANCE

Build toward a structured research graph:

```text
Paper
   ↓
Method
   ↓
Hypothesis
   ↓
Feature
   ↓
Factor
   ↓
Alpha
   ↓
Model
   ↓
Strategy
   ↓
Experiment
   ↓
Trade
   ↓
Outcome
```

Relationships should eventually support:

```text
DERIVED_FROM
USES
TESTED_BY
SUPPORTED_BY
REJECTED_BY
IMPROVES
CONTRADICTS
DEPENDS_ON
```

Do not build a huge graph database immediately.

Establish the domain model and provenance interfaces first.

---

# 33. PERFORMANCE ATTRIBUTION

Every strategy should eventually explain:

```text
Total P&L
├── Market beta
├── Factor exposure
├── Asset selection
├── Timing
├── Sector exposure
├── Volatility exposure
├── Transaction costs
├── Slippage
├── Execution
└── Residual alpha
```

The platform must answer:

> Why did the strategy make or lose money?

---

# 34. REGIME ENGINE

Create a future-ready interface for identifying market regimes.

Possible states:

```text
Bull
Bear
Sideways
High Volatility
Low Volatility
High Liquidity
Low Liquidity
Risk-On
Risk-Off
Crisis
Transition
```

Do not hardcode simplistic regime labels.

Eventually allow statistical regime models:

```text
HMM
Hidden-state models
Clustering
Change-point detection
Volatility regimes
Correlation regimes
```

---

# 35. STRATEGY ONTOLOGY

A strategy must have explicit identity.

Conceptual:

```text
Strategy
│
├── strategy_id
├── name
├── hypothesis
├── alpha dependencies
├── universe
├── frequency
├── holding period
├── entry
├── exit
├── portfolio rules
├── risk profile
├── execution profile
├── model dependencies
├── version
└── lifecycle state
```

---

# 36. DATA → KNOWLEDGE → DECISION → ACTION LOOP

The complete architecture should support:

```text
DATA
 ↓
INFORMATION
 ↓
FEATURES
 ↓
KNOWLEDGE
 ↓
HYPOTHESIS
 ↓
MODEL
 ↓
SIGNAL
 ↓
DECISION
 ↓
RISK
 ↓
ACTION
 ↓
OUTCOME
 ↓
LEARNING
```

This is the central feedback loop of QUANT LAB.

---

# 37. EVENT-DRIVEN ARCHITECTURE

Use explicit event contracts.

Initial event types:

```text
MarketEvent
TickEvent
BarEvent
FundamentalEvent
NewsEvent

FeatureEvent
SignalEvent
ModelEvent

PortfolioEvent
RiskEvent

OrderEvent
ExecutionEvent
FillEvent

ExperimentEvent
ResearchEvent

SystemEvent
AlertEvent
```

Event flow:

```text
MarketEvent
   ↓
MarketState
   ↓
Feature Engine
   ↓
SignalEvent
   ↓
Portfolio Engine
   ↓
RiskEvent
   ↓
OrderEvent
   ↓
Execution Engine
   ↓
Broker
   ↓
ExecutionEvent
   ↓
PortfolioEvent
```

---

# 38. SERVICE BOUNDARIES

Do not create a distributed microservice system prematurely.

Start modular and locally executable.

Preferred initial topology:

```text
Single repository
+
clear package boundaries
+
separate workers where necessary
+
event interfaces
+
database boundaries
```

Only split processes where there is a concrete reason:

```text
long-running trading worker
research worker
data worker
scheduler
API
```

---

# 39. LOCAL-FIRST REQUIREMENT

QUANT LAB should be capable of running locally.

Design for:

```text
Local database
Local datasets
Local research
Local models
Local backtesting
Local AI models where practical
Local broker gateway
```

Cloud integration may be added later.

The architecture must not require a cloud service for basic research.

---

# 40. IP SECURITY

Treat:

```text
research
strategies
alpha
models
datasets
experiments
broker credentials
```

as sensitive assets.

Never log:

```text
API keys
access tokens
secrets
passwords
private credentials
```

Use environment variables/secrets management.

---

# 41. OBSERVABILITY

Implement structured logging.

Every important event should contain:

```text
timestamp
component
event_type
correlation_id
strategy_id
model_id
experiment_id
instrument_id
severity
message
metadata
```

For live trading additionally record:

```text
order_id
broker_order_id
risk_decision_id
execution_id
```

---

# 42. AUDIT TRAIL

The system must eventually provide an immutable audit trail:

```text
WHO
WHAT
WHEN
WHY
WITH WHICH DATA
WITH WHICH MODEL
UNDER WHICH CONFIGURATION
WITH WHICH RISK LIMITS
WHAT ACTION
WHAT RESULT
```

This is mandatory for serious live deployment.

---

# 43. CONFIGURATION

Avoid scattered constants.

Use structured configuration.

Separate:

```text
system config
market config
data config
research config
model config
portfolio config
risk config
execution config
broker config
AI config
```

Environment-specific configuration:

```text
development
research
paper
shadow
production
```

---

# 44. TESTING

Every core component must have tests.

Minimum:

```text
Unit tests
Integration tests
Backtest tests
Risk tests
Execution tests
Broker adapter tests
Data integrity tests
Reconciliation tests
Failure recovery tests
End-to-end tests
```

Add property-based testing where useful.

---

# 45. CRITICAL FAILURE TESTS

Explicitly test:

```text
stale data
missing data
duplicate data
timestamp error
bad corporate action
broker timeout
broker disconnect
duplicate order
partial fill
unknown order state
position mismatch
database outage
risk engine outage
model outage
AI outage
invalid configuration
market closed
unexpected broker position
```

Expected principle:

```text
UNCERTAINTY
   ↓
FAIL CLOSED
   ↓
NO NEW LIVE RISK
```

---

# 46. FIRST IMPLEMENTATION PRIORITY

Do not attempt the entire system immediately.

Build a vertical slice.

Target:

```text
Historical Data
      ↓
Data Validation
      ↓
MarketState
      ↓
Feature
      ↓
Signal
      ↓
Portfolio
      ↓
Risk
      ↓
Backtest
      ↓
Performance
      ↓
Experiment Ledger
```

This must work before adding sophisticated AI.

---

# 47. FIRST RESEARCH STRATEGY

Use a simple deterministic strategy as the architectural test.

Recommended:

```text
Cross-sectional momentum
```

or another simple mathematically defined factor.

The goal is NOT profitability.

The goal is proving:

```text
data
→ feature
→ signal
→ portfolio
→ risk
→ execution simulation
→ P&L
→ experiment
```

is reproducible.

---

# 48. FIRST MODEL BENCHMARK

Use simple baselines before sophisticated AI:

```text
Buy-and-hold
Equal-weight
Simple momentum
Simple mean-reversion
Linear regression
Tree-based model
```

This establishes a benchmark hierarchy.

A complex model must beat meaningful baselines after realistic costs and validation.

---

# 49. RESEARCH METRICS

At minimum calculate:

```text
CAGR
Total Return
Volatility
Sharpe
Sortino
Maximum Drawdown
Calmar
Win Rate
Profit Factor
Turnover
Average Holding Period
Exposure
Beta
Alpha
Transaction Costs
Slippage
Capacity estimate
```

Also calculate stability across:

```text
years
regimes
sectors
market-cap buckets
volatility states
```

---

# 50. DO NOT OPTIMIZE ONLY FOR SHARPE

A strategy should be evaluated across:

```text
Return
Risk
Stability
Capacity
Turnover
Liquidity
Drawdown
Cost sensitivity
Parameter sensitivity
Regime sensitivity
Out-of-sample performance
```

A high backtest Sharpe with unstable parameters should be treated as suspicious.

---

# 51. MULTIPLE-HYPOTHESIS CONTROL

The Alpha Factory will eventually test thousands/millions of candidate signals.

Therefore architecture must eventually support:

```text
multiple testing awareness
false discovery control
research family tracking
experiment genealogy
out-of-sample confirmation
```

Do not treat the best result among thousands of experiments as automatically meaningful.

---

# 52. STRATEGY CORRELATION

The system should eventually measure whether multiple strategies are actually independent.

Build toward:

```text
Strategy return correlation
Factor correlation
Signal correlation
Drawdown correlation
Regime correlation
Tail correlation
```

The objective is not simply:

```text
100 strategies
```

but:

```text
many sufficiently independent sources of risk-adjusted return
```

---

# 53. CAPITAL ALLOCATION

The system should eventually allocate capital across strategies.

Conceptual:

```text
Alpha A
Alpha B
Alpha C
Alpha D
     ↓
Strategy-level risk
     ↓
Correlation
     ↓
Portfolio optimizer
     ↓
Capital allocation
```

This becomes a higher-level portfolio of strategies.

---

# 54. EXECUTION AS A SOURCE OF ALPHA

Treat execution separately from prediction.

Research:

```text
signal alpha
+
execution alpha
```

Execution research may eventually include:

```text
TWAP
VWAP
POV
Adaptive execution
Liquidity-aware execution
Market-impact minimization
Spread capture
Latency analysis
```

Do not implement HFT prematurely.

Build interfaces first.

---

# 55. RESEARCH DASHBOARD

The UI eventually needs:

```text
Market Dashboard
Research Lab
MarketState Explorer
Feature Lab
Factor Lab
Alpha Lab
Model Lab
Experiment Lab
Backtest Lab
Portfolio Lab
Risk Console
Execution Console
Broker Console
AI Research Console
Performance Attribution
Audit Trail
System Health
```

Prioritize functionality over visual polish during the first development stage.

---

# 56. REFERENCE REPOSITORY MAPPING

After the first repository study, create a mapping:

```text
Qlib
→ Research architecture

OpenBB
→ Data/provider architecture

VN.Py
→ Event/trading architecture

Hummingbot
→ Execution architecture

StockSharp
→ Trading-domain architecture

OpenAlgo
→ Indian broker abstraction

QuantDinger
→ Worker/process/observability architecture

Lumibot
→ Strategy lifecycle

TradingAgents
→ AI research organization

AI Hedge Fund
→ Agent-based alpha concepts

Stefan Jansen
→ Quant/ML research methodology

Financial ML
→ Advanced quantitative methodology

AKShare
→ Data acquisition reference
```

For every borrowed concept document:

```text
Reference
Concept
Why useful
QUANT LAB implementation
Differences
Risks
License implications
```

---

# 57. LICENSE COMPLIANCE

Before incorporating any external code/dependency:

1. inspect its license;
2. determine compatibility;
3. document it;
4. preserve required notices;
5. do not copy code merely because it is open source.

Prefer independent implementations of architectural ideas.

---

# 58. CODING STYLE

Use:

```text
Python
Type hints
Pydantic for contracts where appropriate
NumPy/SciPy for numerical primitives
Polars/pandas where appropriate
PostgreSQL
Parquet
DuckDB
Redis where appropriate
FastAPI
Pytest
Ruff
```

Do not add dependencies merely because a reference repository uses them.

Every dependency should have a reason.

---

# 59. PERFORMANCE PHILOSOPHY

First:

```text
correctness
```

Then:

```text
reproducibility
```

Then:

```text
profiling
```

Then:

```text
optimization
```

Do not prematurely rewrite everything in C++/Rust.

Use native acceleration only where profiling demonstrates a real bottleneck.

---

# 60. ENGINEERING PRINCIPLE: DOMAIN ≠ INFRASTRUCTURE

The following should remain independent:

```text
Domain
Research
Broker
Database
UI
AI
```

For example:

```text
Alpha
```

must not know:

```text
PostgreSQL
Zerodha
React
OpenAI
Redis
```

Similarly:

```text
ZerodhaAdapter
```

must not know:

```text
how an alpha was generated
```

---

# 61. ENGINEERING PRINCIPLE: SAME STRATEGY, MULTIPLE RUNTIMES

Eventually:

```text
Strategy
  │
  ├── Backtest Runtime
  ├── Paper Runtime
  ├── Shadow Runtime
  └── Live Runtime
```

The strategy logic should remain as consistent as possible.

Only environment/execution infrastructure should change.

---

# 62. RESEARCH ARTIFACT VERSIONING

Version:

```text
datasets
features
factors
signals
models
strategies
risk configurations
execution configurations
experiments
```

A result without versions is not reproducible research.

---

# 63. RESEARCH STATUS MACHINE

For hypotheses/alphas:

```text
IDEA
 ↓
FORMALIZED
 ↓
EXPERIMENTAL
 ↓
PROMISING
 ↓
ROBUST
 ↓
PAPER
 ↓
LIVE_CANDIDATE
 ↓
LIVE
 ↓
DEGRADED
 ↓
RETIRED
```

Rejected ideas:

```text
REJECTED
```

must remain searchable.

---

# 64. MODEL/ALPHA RETIREMENT

A live strategy must have monitoring for:

```text
performance degradation
distribution shift
feature drift
regime change
execution degradation
liquidity deterioration
risk increase
```

Potential future state:

```text
ACTIVE
 ↓
DEGRADED
 ↓
REVIEW
 ↓
RESTRICTED
 ↓
RETIRED
```

---

# 65. NO BLACK BOX LIVE DEPLOYMENT

Before any strategy reaches live trading, QUANT LAB must be able to explain:

```text
What is the hypothesis?
What data does it use?
What is the signal?
What is the expected behavior?
What are the risks?
What is the validation evidence?
What are the failure conditions?
What capital limits apply?
How is it executed?
```

---

# 66. HUMAN OVERSIGHT

The architecture should support explicit human approval gates.

Especially:

```text
Research → Paper
Paper → Shadow
Shadow → Live
```

and potentially:

```text
Live strategy parameter changes
Risk limit changes
Capital allocation changes
Broker changes
```

---

# 67. DEVELOPMENT ORDER — IMMEDIATE

Continue from the state produced by Prompt 01.

Do this sequence:

## STEP A — Inspect Current Workspace

Determine:

```text
What Prompt 01 created
What is complete
What is incomplete
What architecture exists
What conflicts with this directive
```

Do not delete useful work.

---

## STEP B — Architecture Reconciliation

Create:

```text
docs/architecture/QUANT_LAB_ARCHITECTURE_RECONCILIATION.md
```

Compare:

```text
Prompt 01 architecture
+
Existing workspace
+
Previously defined QUANT LAB architecture
+
Repository findings
```

Output:

```text
KEEP
CHANGE
ADD
REMOVE
DEFER
```

---

## STEP C — Architecture Freeze Candidate

Create:

```text
docs/architecture/QUANT_LAB_TARGET_ARCHITECTURE_v0.2.md
```

Include:

```text
system context
domain model
component model
data flow
research flow
AI flow
risk flow
execution flow
deployment
security
observability
```

---

## STEP D — Domain Foundation

Implement first:

```text
Instrument
MarketEvent
MarketState
Feature
Factor
Signal
SignalGenome
ResearchHypothesis
Alpha
Model
Strategy
Portfolio
Position
Order
Execution
RiskDecision
Experiment
```

---

## STEP E — Vertical Research Slice

Implement:

```text
Historical Data
   ↓
MarketState
   ↓
Feature
   ↓
Momentum Signal
   ↓
Portfolio
   ↓
Risk
   ↓
Backtest
   ↓
Metrics
   ↓
Experiment Registry
```

---

## STEP F — Test

Run:

```text
lint
type checks
unit tests
integration tests
backtest tests
research-integrity tests
```

Fix errors.

---

# 68. DO NOT BUILD YET

Do NOT spend the initial implementation cycle on:

```text
autonomous live AI trading
reinforcement learning
HFT
complex neural architectures
massive multi-agent systems
beautiful dashboards
mobile applications
dozens of broker integrations
hundreds of indicators
cloud deployment
```

First prove the scientific core.

---

# 69. SUCCESS CRITERIA FOR THIS STAGE

The stage is complete when QUANT LAB can demonstrate:

```text
1. Load historical data.
2. Validate the data.
3. Construct MarketState.
4. Calculate a feature.
5. Generate a deterministic signal.
6. Convert signal → target portfolio.
7. Apply risk constraints.
8. Run a realistic backtest.
9. Calculate performance metrics.
10. Run research-integrity checks.
11. Register the experiment.
12. Reproduce the same experiment.
13. Explain where the result came from.
```

No live money is required.

---

# 70. FINAL OPERATING DIRECTIVE TO CURSOR

You are now working as the **principal architect, quantitative researcher, and senior software engineer** for QUANT LAB.

When implementing anything:

```text
UNDERSTAND
   ↓
INSPECT
   ↓
COMPARE
   ↓
DESIGN
   ↓
DOCUMENT
   ↓
IMPLEMENT
   ↓
TEST
   ↓
VALIDATE
   ↓
PROFILE
   ↓
REPORT
```

Never optimize for code volume.

Optimize for:

```text
Scientific correctness
Reproducibility
Research integrity
Modularity
Auditability
Risk containment
Extensibility
Performance
Security
```

If you encounter an architectural conflict:

```text
STOP
 ↓
DOCUMENT
 ↓
COMPARE OPTIONS
 ↓
CHOOSE
 ↓
CREATE ADR
 ↓
IMPLEMENT
```

Do not silently make major architectural decisions.

---

# 71. THE ULTIMATE QUANT LAB LOOP

The final system should evolve toward:

```text
                  ┌───────────────────────────┐
                  │       REAL MARKET         │
                  └─────────────┬─────────────┘
                                ↓
                           DATA FABRIC
                                ↓
                           MARKET STATE
                                ↓
                       QUANT REPRESENTATION
                                ↓
                      AI + HUMAN HYPOTHESES
                                ↓
                         ALPHA FACTORY
                                ↓
                         SIGNAL GENOME
                                ↓
                       EXPERIMENT ENGINE
                                ↓
                    RESEARCH INTEGRITY ENGINE
                                ↓
                         MODEL FACTORY
                                ↓
                       PORTFOLIO ENGINE
                                ↓
                          RISK FIREWALL
                                ↓
                       EXECUTION ENGINE
                                ↓
                       BROKER / MARKET
                                ↓
                           REAL P&L
                                ↓
                     PERFORMANCE ATTRIBUTION
                                ↓
                         REGIME ANALYSIS
                                ↓
                         RESEARCH MEMORY
                                │
                                └───────────────┐
                                                ↓
                                      NEXT HYPOTHESIS
```

This feedback loop is the heart of QUANT LAB.

---

# 72. FINAL PRINCIPLE

**Do not build an AI that guesses stocks.**

Build a system that can:

```text
OBSERVE
MEASURE
MODEL
HYPOTHESIZE
EXPERIMENT
FALSIFY
DISCOVER
VALIDATE
OPTIMIZE
CONTROL
EXECUTE
LEARN
```

The long-term objective is a system where AI expands the **research search space**, mathematics determines the structure of the hypothesis, statistics determines whether evidence exists, risk determines what can be traded, and the execution engine determines how it is traded.

That is QUANT LAB.

**CONTINUE FROM THE CURRENT WORKSPACE.**
**DO NOT RESET THE PROJECT.**
**DO NOT WAIT FOR ANOTHER PROMPT AFTER COMPLETING THE ABOVE RECONCILIATION AND FIRST VERTICAL SLICE.**
