# QUANT LAB — Cursor Coding Agent Master Instruction
## Repository Reverse-Engineering + Greenfield Implementation Directive
### Version 0.1 — Build Start: 2026-08-30

> **MISSION:** Start building QUANT LAB today.
>
> This document is the master instruction for the Cursor coding agent. It defines how the agent must study the supplied open-source repositories, extract architectural patterns, and implement QUANT LAB as a new, original, local-first quantitative research and trading platform.
>
> **IMPORTANT:** Do NOT copy repository code, proprietary implementation details, branding, or large code sections. Reverse-engineer architecture, interfaces, algorithms, engineering patterns, failure modes, and design principles. Reimplement the required functionality independently.

---

# 1. PROJECT OBJECTIVE

Build **QUANT LAB**, a serious quantitative research and trading laboratory designed initially for the **Indian equity and derivatives market**, with a future path toward multi-asset and multi-broker operation.

QUANT LAB must not be designed as:

- a simple stock screener;
- an LLM stock-picking chatbot;
- a collection of technical indicators;
- a single monolithic trading bot;
- a copied Qlib/OpenBB/VN.Py/OpenAlgo application.

QUANT LAB must become a:

> **Local-first quantitative research, alpha discovery, portfolio construction, risk management, backtesting, paper-trading, and controlled live-execution operating system.**

The architectural philosophy is:

```text
DATA
  ↓
DATA INTEGRITY
  ↓
RESEARCH
  ↓
FEATURES / FACTORS
  ↓
ALPHA DISCOVERY
  ↓
MODEL FACTORY
  ↓
VALIDATION
  ↓
PORTFOLIO CONSTRUCTION
  ↓
RISK AUTHORIZATION
  ↓
EXECUTION
  ↓
BROKER
  ↓
PERFORMANCE ATTRIBUTION
  ↓
RESEARCH FEEDBACK
```

AI is an assisting intelligence layer across this pipeline, not an unrestricted trading authority.

---

# 2. PRIMARY REFERENCE REPOSITORIES

The agent MUST inspect and study these repositories.

## 2.1 Core research/data/trading platforms

1. https://github.com/OpenBB-finance/OpenBB.git
2. https://github.com/microsoft/qlib.git
3. https://github.com/hummingbot/hummingbot.git
4. https://github.com/OpenByteInc/QuantDinger.git
5. https://github.com/StockSharp/StockSharp.git
6. https://github.com/vnpy/vnpy.git
7. https://github.com/akfamily/akshare.git
8. https://github.com/marketcalls/openalgo.git
9. https://github.com/lumiwealth/lumibot.git

## 2.2 Quant/ML research references

10. https://github.com/stefan-jansen/machine-learning-for-trading.git
11. https://github.com/firmai/financial-machine-learning.git
12. https://github.com/purvasingh96/AI-for-Trading.git
13. https://github.com/wilsonfreitas/awesome-quant.git

## 2.3 AI trading research/agent references

14. https://github.com/HKUDS/AI-Trader.git
15. https://github.com/virattt/ai-hedge-fund.git
16. https://github.com/TauricResearch/TradingAgents.git
17. https://github.com/ZhuLinsen/daily_stock_analysis.git

## 2.4 Specialized references

18. https://github.com/OpenByteInc/QuantDinger.git
19. https://github.com/RyanCodrai/turbovec.git
20. https://github.com/Cortex-AI-Quant/crypto-arbitrage-bot-automated-trading.git

The duplicate appearance of any repository must be treated as one source.

---

# 3. REVERSE-ENGINEERING RULE

Do not begin by blindly writing QUANT LAB code.

First establish a technical understanding of the reference ecosystem.

For every repository determine:

```text
Repository
├── License
├── Primary purpose
├── Technology stack
├── Directory architecture
├── Core modules
├── Core domain objects
├── Interfaces / abstractions
├── Data model
├── Data ingestion
├── Feature engineering
├── Research workflow
├── ML workflow
├── Backtesting
├── Portfolio construction
├── Risk management
├── Order management
├── Execution
├── Broker/exchange adapters
├── Event architecture
├── Scheduling
├── Persistence
├── Caching
├── API architecture
├── UI architecture
├── AI/agent architecture
├── Observability
├── Testing
├── Security
├── Deployment
├── Strengths
├── Weaknesses
├── Scalability limitations
└── Lessons for QUANT LAB
```

Do not merely summarize README files.

Inspect source directories, important classes/functions, interfaces, tests, configuration, examples, and architectural documentation.

---

# 4. REPOSITORY STUDY PRIORITY

Study repositories in this order.

## Tier 1 — Architecture

### Qlib
Study deeply:

- data layer;
- dataset abstractions;
- feature pipeline;
- model interfaces;
- workflow;
- backtesting;
- portfolio construction;
- risk;
- experiment tracking;
- configuration;
- extensibility.

### OpenBB
Study deeply:

- provider abstraction;
- data normalization;
- command/API organization;
- extension architecture;
- data model;
- AI/MCP interfaces;
- separation between data providers and consumers.

### VN.Py
Study deeply:

- event engine;
- gateway abstraction;
- strategy engine;
- order lifecycle;
- portfolio concepts;
- backtesting;
- algorithmic execution;
- modular apps.

### Hummingbot
Study deeply:

- connectors;
- strategy/executor separation;
- event-driven execution;
- order lifecycle;
- execution algorithms;
- state handling.

### StockSharp
Study deeply:

- instrument abstraction;
- market data;
- trading connections;
- order management;
- strategies;
- backtesting;
- portfolio;
- data storage;
- modularity.

### OpenAlgo
Study deeply:

- Indian broker abstraction;
- unified API;
- order APIs;
- market data;
- broker adapters;
- paper trading;
- analyzer;
- execution architecture;
- security boundaries.

---

# 5. SECONDARY REPOSITORY STUDY

## QuantDinger

Study:

- process separation;
- trading worker;
- scheduler worker;
- asynchronous jobs;
- durable state;
- Redis usage;
- PostgreSQL;
- observability;
- audit logs;
- security;
- deployment hardening.

Extract architectural principles, not code.

## Lumibot

Study:

- strategy abstraction;
- backtest/live equivalence;
- broker interfaces;
- AI agent runtime;
- deterministic/AI hybrid strategies.

## TradingAgents

Study:

- multi-agent role decomposition;
- research agents;
- bull/bear reasoning;
- risk agents;
- portfolio manager;
- decision logs;
- checkpoint/recovery.

## AI Hedge Fund

Study:

- agent-as-alpha concepts;
- investment committee structure;
- model modularity;
- persistent reasoning.

Treat it primarily as a research/experimental reference.

## daily_stock_analysis

Study:

- automated research reports;
- data/news aggregation;
- fundamental/technical analysis;
- AI research workflow.

## Stefan Jansen / financial-machine-learning / AI-for-Trading

Study as methodology/reference material:

- feature engineering;
- factor modeling;
- labels;
- time-series validation;
- walk-forward testing;
- financial ML;
- portfolio construction;
- risk;
- alternative data;
- avoiding leakage;
- research workflow.

## awesome-quant

Use as an ecosystem index.

Do not attempt to implement everything listed there.

---

# 6. NON-NEGOTIABLE ARCHITECTURAL PRINCIPLE

QUANT LAB must be **research-first**, not AI-first.

Correct:

```text
Market Data
    ↓
Quantitative Evidence
    ↓
Statistical/ML Model
    ↓
Signal
    ↓
Portfolio
    ↓
Risk
    ↓
Execution
```

AI assists:

```text
AI
├── Research assistant
├── Literature assistant
├── Hypothesis generator
├── Feature discovery assistant
├── Code generation assistant
├── Experiment analyst
├── Model critic
├── Red-team researcher
├── News/sentiment analyst
├── Portfolio analyst
└── Performance analyst
```

AI must NOT bypass:

```text
Risk Engine
Execution Rules
Position Limits
Loss Limits
Data Integrity
Validation Gates
Human Authorization
```

---

# 7. TARGET QUANT LAB ARCHITECTURE

Create a modular monorepo.

Initial target:

```text
quant-lab/
│
├── README.md
├── LICENSE
├── pyproject.toml
├── .gitignore
├── .env.example
├── docker-compose.yml
│
├── docs/
│   ├── architecture/
│   ├── research/
│   ├── data/
│   ├── execution/
│   ├── risk/
│   ├── ai/
│   └── decisions/
│
├── apps/
│   ├── api/
│   ├── web/
│   ├── research/
│   └── trading/
│
├── packages/
│   │
│   ├── core/
│   │   ├── config/
│   │   ├── logging/
│   │   ├── errors/
│   │   ├── events/
│   │   ├── time/
│   │   ├── units/
│   │   └── identifiers/
│   │
│   ├── domain/
│   │   ├── instruments/
│   │   ├── market/
│   │   ├── orders/
│   │   ├── executions/
│   │   ├── portfolio/
│   │   ├── positions/
│   │   ├── strategies/
│   │   ├── models/
│   │   ├── experiments/
│   │   └── risk/
│   │
│   ├── data/
│   │   ├── contracts/
│   │   ├── providers/
│   │   ├── normalization/
│   │   ├── validation/
│   │   ├── corporate_actions/
│   │   ├── point_in_time/
│   │   ├── storage/
│   │   └── lineage/
│   │
│   ├── research/
│   │   ├── datasets/
│   │   ├── features/
│   │   ├── factors/
│   │   ├── labels/
│   │   ├── alpha/
│   │   ├── statistics/
│   │   ├── timeseries/
│   │   ├── machine_learning/
│   │   ├── deep_learning/
│   │   └── experiments/
│   │
│   ├── models/
│   │   ├── registry/
│   │   ├── training/
│   │   ├── validation/
│   │   ├── selection/
│   │   ├── ensembles/
│   │   └── drift/
│   │
│   ├── portfolio/
│   │   ├── construction/
│   │   ├── optimization/
│   │   ├── allocation/
│   │   ├── rebalancing/
│   │   └── attribution/
│   │
│   ├── risk/
│   │   ├── limits/
│   │   ├── exposure/
│   │   ├── volatility/
│   │   ├── var/
│   │   ├── cvar/
│   │   ├── drawdown/
│   │   ├── liquidity/
│   │   ├── stress/
│   │   └── firewall/
│   │
│   ├── backtest/
│   │   ├── engine/
│   │   ├── broker_sim/
│   │   ├── slippage/
│   │   ├── transaction_costs/
│   │   ├── latency/
│   │   ├── market_impact/
│   │   └── analytics/
│   │
│   ├── execution/
│   │   ├── engine/
│   │   ├── orders/
│   │   ├── algorithms/
│   │   ├── reconciliation/
│   │   └── state/
│   │
│   ├── brokers/
│   │   ├── interface.py
│   │   ├── zerodha/
│   │   ├── openalgo/
│   │   └── paper/
│   │
│   ├── ai/
│   │   ├── agents/
│   │   ├── tools/
│   │   ├── memory/
│   │   ├── research/
│   │   ├── critics/
│   │   ├── orchestration/
│   │   └── permissions/
│   │
│   ├── knowledge/
│   │   ├── papers/
│   │   ├── methods/
│   │   ├── factors/
│   │   ├── strategies/
│   │   └── research_memory/
│   │
│   └── observability/
│       ├── metrics/
│       ├── tracing/
│       ├── audit/
│       └── monitoring/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── research/
│   ├── backtest/
│   ├── execution/
│   ├── risk/
│   └── end_to_end/
│
├── scripts/
│   ├── data/
│   ├── research/
│   ├── backtest/
│   └── deployment/
│
└── notebooks/
    ├── research/
    ├── factors/
    ├── models/
    └── validation/
```

The agent may improve this structure after repository analysis, but MUST document architectural changes before making major deviations.

---

# 8. CANONICAL DOMAIN MODEL

Define stable domain objects.

At minimum:

```text
Instrument
MarketEvent
OHLCVBar
Tick
OrderBookSnapshot
CorporateAction
FundamentalObservation
NewsEvent

Feature
Factor
Label
Dataset
Model
ModelVersion
Signal

Strategy
Portfolio
Position
TargetPosition

Order
Execution
Fill
BrokerAccount

RiskLimit
RiskDecision

Experiment
ExperimentRun
Backtest
BacktestResult

ResearchHypothesis
ResearchArtifact
Alpha
```

These objects must not be tightly coupled to one broker or one data vendor.

---

# 9. DATA FABRIC

Implement a provider-neutral interface.

Example conceptual interface:

```python
class MarketDataProvider(Protocol):
    def get_bars(...): ...
    def get_ticks(...): ...
    def get_instruments(...): ...
    def get_fundamentals(...): ...
```

Providers should include adapters rather than infecting the research layer with vendor-specific APIs.

Initial Indian-market targets:

```text
NSE
BSE
Zerodha/Kite
OpenAlgo
Other providers as adapters
```

Do not hardcode credentials.

---

# 10. POINT-IN-TIME DATA IS MANDATORY

The system must explicitly account for:

- publication timestamps;
- effective timestamps;
- trading timestamps;
- corporate actions;
- historical universe membership;
- delisted securities;
- survivorship bias;
- restated fundamentals;
- data revisions.

Never construct a historical dataset using information that was unavailable at that historical time.

Implement a clear distinction between:

```text
event_time
effective_time
available_time
ingestion_time
```

---

# 11. RESEARCH INTEGRITY ENGINE

This is a core differentiator.

Implement validation for:

```text
Look-ahead bias
Data leakage
Survivorship bias
Selection bias
Train/test contamination
Timestamp leakage
Feature leakage
Corporate-action leakage
Multiple testing
Parameter overfitting
Regime overfitting
Liquidity assumptions
Transaction-cost assumptions
Slippage assumptions
Execution latency
```

Every experiment must record whether these checks passed.

---

# 12. EXPERIMENT LEDGER

Every experiment must be reproducible.

Store:

```text
Experiment ID
Git commit
Dataset version
Universe
Feature versions
Label definition
Model version
Hyperparameters
Training period
Validation period
Test period
Transaction-cost model
Slippage model
Execution assumptions
Random seeds
Environment information
Metrics
Risk metrics
Artifacts
Logs
Research hypothesis
Conclusion
```

The same experiment must be reproducible from its metadata.

---

# 13. BACKTEST ENGINE

Do not implement a naïve:

```python
for day in data:
    signal = strategy(...)
    portfolio += signal
```

only.

The backtester must eventually support:

```text
Market events
Order events
Execution events
Latency
Slippage
Transaction costs
Partial fills
Order queue
Liquidity
Position constraints
Portfolio accounting
Corporate actions
Broker rules
Trading hours
Auction/market behavior where applicable
```

Build the first implementation incrementally.

---

# 14. STRATEGY INTERFACE

Create a broker-neutral strategy interface.

Conceptually:

```python
class Strategy(Protocol):
    def on_start(self, context): ...
    def on_market_event(self, event): ...
    def generate_signal(self, context): ...
    def target_positions(self, context): ...
    def on_order_update(self, update): ...
    def on_stop(self, context): ...
```

Strategies should not directly depend on:

```text
Kite API
OpenAlgo API
specific database
specific UI
LLM provider
```

---

# 15. PORTFOLIO ENGINE

Separate:

```text
Signal
    ≠
Target Position
    ≠
Order
    ≠
Execution
```

Correct pipeline:

```text
Signal
 ↓
Signal normalization
 ↓
Portfolio construction
 ↓
Target positions
 ↓
Risk checks
 ↓
Execution planning
 ↓
Orders
 ↓
Fills
 ↓
Portfolio state
```

---

# 16. RISK FIREWALL

This is NON-NEGOTIABLE.

No AI agent, strategy, notebook, API endpoint, or UI action may bypass the risk firewall.

Conceptual flow:

```text
Proposed Trade
      ↓
Instrument Validation
      ↓
Account Validation
      ↓
Position Limit
      ↓
Exposure Limit
      ↓
Liquidity Check
      ↓
Loss Limit
      ↓
Portfolio Risk
      ↓
Market Condition Check
      ↓
Broker Constraints
      ↓
Risk Decision
      ↓
APPROVE / MODIFY / REJECT
```

Risk decisions must be logged.

---

# 17. EXECUTION ENGINE

Separate execution from strategy.

Implement an abstraction such as:

```python
class ExecutionEngine:
    def submit(...)
    def cancel(...)
    def modify(...)
    def reconcile(...)
```

And:

```python
class BrokerGateway:
    def get_account(...)
    def get_positions(...)
    def get_orders(...)
    def place_order(...)
    def cancel_order(...)
    def modify_order(...)
```

First-class order states:

```text
CREATED
VALIDATING
APPROVED
REJECTED
SUBMITTED
ACKNOWLEDGED
PARTIALLY_FILLED
FILLED
CANCEL_REQUESTED
CANCELLED
FAILED
UNKNOWN
RECONCILING
```

Never assume an order succeeded merely because an API request returned successfully.

---

# 18. ZERODHA / OPENALGO

The first production broker path should be designed around a broker-neutral interface.

Target:

```text
QUANT LAB
   ↓
Broker Interface
   ↓
OpenAlgo / Zerodha Adapter
   ↓
Broker
```

Do not allow broker-specific logic into strategy code.

Live execution must initially be disabled by default.

Use:

```text
RESEARCH
→ BACKTEST
→ PAPER
→ SHADOW
→ LIVE
```

as the promotion path.

---

# 19. AI ARCHITECTURE

AI must be modular.

Create:

```text
ResearchAgent
DataAnalystAgent
FeatureResearchAgent
AlphaResearchAgent
ModelAnalystAgent
BullResearcher
BearResearcher
RiskReviewer
PortfolioAnalyst
ExecutionReviewer
PerformanceAnalyst
ResearchCritic
```

But these are **assistive components**.

The AI permission system must explicitly define:

```text
READ_DATA
WRITE_RESEARCH
RUN_EXPERIMENT
CREATE_STRATEGY
RUN_BACKTEST
REQUEST_PAPER_ORDER
REQUEST_LIVE_ORDER
```

Only authorized deterministic services may approve live trading.

---

# 20. AI SHOULD HELP DISCOVER ALPHA

The intended research loop:

```text
AI generates hypothesis
        ↓
Quant researcher formalizes hypothesis
        ↓
Feature/label definition
        ↓
Historical test
        ↓
Statistical validation
        ↓
ML validation
        ↓
Walk-forward
        ↓
Robustness testing
        ↓
Transaction-cost testing
        ↓
Portfolio simulation
        ↓
Research report
        ↓
Human/model review
```

Do not let the LLM declare an alpha “valid” merely because a backtest is profitable.

---

# 21. ALPHA FACTORY

Design a standardized alpha interface.

An alpha should specify:

```text
Name
Hypothesis
Universe
Data dependencies
Features
Formula/model
Prediction horizon
Expected holding period
Signal direction
Neutralization
Constraints
Validation method
Research status
Model version
```

Future alpha families:

```text
Momentum
Mean Reversion
Value
Quality
Growth
Volatility
Liquidity
Microstructure
Statistical Arbitrage
Pairs
Cross-sectional
Time-series
Event-driven
Options
Market regime
Alternative data
```

---

# 22. MATHEMATICAL CORE

Do not rely exclusively on technical indicators.

Build toward:

```text
Probability
Statistics
Linear Algebra
Optimization
Time-Series Analysis
Stochastic Processes
Bayesian Inference
Information Theory
Signal Processing
Econometrics
Machine Learning
Portfolio Theory
Market Microstructure
```

Potential advanced research modules:

```text
Kalman Filters
Hidden Markov Models
State-space models
Cointegration
PCA
ICA
Clustering
Graph models
Regime detection
Factor models
Shrinkage covariance
Robust optimization
Bayesian models
Online learning
Reinforcement learning
Evolutionary search
Symbolic regression
Information-theoretic alpha discovery
```

Do not implement advanced mathematics prematurely. Establish clean interfaces first.

---

# 23. PERFORMANCE ATTRIBUTION

The system must eventually explain P&L.

Decompose:

```text
Total P&L
├── Asset selection
├── Factor exposure
├── Timing
├── Sector exposure
├── Market beta
├── Volatility
├── Transaction costs
├── Slippage
├── Execution
└── Residual alpha
```

For every strategy, answer:

> Why did we make or lose money?

---

# 24. OBSERVABILITY

Trading systems require operational observability.

Implement:

```text
Structured logs
Metrics
Audit trail
Order lifecycle logs
Risk decisions
Model decisions
Agent decisions
Latency measurements
Data freshness
Broker connectivity
Position reconciliation
Error rates
```

The system must be able to answer:

```text
What did the system know?
When did it know it?
What model was active?
What signal was generated?
Why was the trade proposed?
What risk checks ran?
Why was it approved/rejected?
What order was sent?
What happened at the broker?
What was filled?
What was the resulting P&L?
```

---

# 25. SECURITY

Never commit:

```text
API keys
Broker secrets
Tokens
Passwords
Private credentials
```

Use environment variables/secrets management.

Live trading must require explicit configuration.

Default:

```text
LIVE_TRADING=false
```

Add a hard safety mechanism.

For example:

```text
LIVE_TRADING_ENABLED
+
BROKER_CONNECTED
+
RISK_ENGINE_HEALTHY
+
STRATEGY_APPROVED
+
MODEL_APPROVED
+
DATA_HEALTHY
+
SESSION_VALID
```

All required conditions must pass.

---

# 26. TESTING STANDARD

Every major module requires tests.

Minimum categories:

```text
Unit
Integration
Property-based where appropriate
Historical-data tests
Backtest tests
Risk tests
Execution tests
Broker adapter tests
Failure/recovery tests
End-to-end tests
```

Especially test:

```text
Order duplication
Partial fills
Network timeout
Broker disconnect
Stale data
Wrong timestamps
Missing bars
Market closure
Position mismatch
Unexpected broker state
Risk limit breach
Model unavailable
AI unavailable
Database failure
```

---

# 27. FAILURE PHILOSOPHY

Trading infrastructure must fail closed.

If:

```text
Data unavailable
Risk engine unavailable
Broker state uncertain
Position reconciliation failed
Model state corrupted
Configuration invalid
```

then:

```text
NO NEW LIVE ORDERS
```

unless a specifically designed emergency procedure permits otherwise.

---

# 28. DATABASE STRATEGY

Initial recommendation:

```text
PostgreSQL
    ↓
Canonical operational state

Parquet
    ↓
Historical research datasets

DuckDB
    ↓
Fast analytical research queries

Redis
    ↓
Cache / transient coordination
```

Do not make Redis the source of truth for financial state.

---

# 29. EVENT-DRIVEN DESIGN

Use an internal event model.

Example:

```text
MarketEvent
DataEvent
SignalEvent
RiskEvent
OrderEvent
ExecutionEvent
PortfolioEvent
ModelEvent
ExperimentEvent
SystemEvent
```

Possible flow:

```text
MarketEvent
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
Broker
   ↓
ExecutionEvent
   ↓
PortfolioEvent
```

---

# 30. UI REQUIREMENTS

The UI should eventually provide:

```text
Dashboard
Market Explorer
Research Lab
Dataset Explorer
Feature Lab
Factor Lab
Alpha Lab
Model Lab
Backtest Lab
Portfolio Lab
Risk Console
Execution Console
Broker Console
Experiment Registry
AI Research Console
Performance Attribution
System Health
Audit Trail
```

Do not spend the first development phase polishing UI while the quant core is incomplete.

---

# 31. DEVELOPMENT PHASES

## PHASE 0 — Repository Intelligence

Before major implementation:

1. Inspect all reference repositories.
2. Build a repository comparison matrix.
3. Identify common abstractions.
4. Identify conflicting architectural decisions.
5. Identify mature implementations.
6. Identify weaknesses.
7. Create `docs/reference/REPOSITORY_STUDY.md`.
8. Create `docs/reference/ARCHITECTURE_DECISION_MATRIX.md`.

---

## PHASE 1 — QUANT LAB Skeleton

Implement:

```text
monorepo
core
domain
data
research
models
portfolio
risk
backtest
execution
brokers
AI
observability
tests
```

Ensure imports and package boundaries are clean.

---

## PHASE 2 — Canonical Domain

Implement:

```text
Instrument
MarketEvent
Bar
Order
Execution
Position
Portfolio
Signal
Strategy
RiskDecision
Experiment
Model
```

with validation and serialization.

---

## PHASE 3 — Data Fabric

Implement:

```text
provider interface
normalization
validation
storage
dataset versioning
point-in-time foundations
```

Start with a small controlled dataset.

Do not attempt every market/provider immediately.

---

## PHASE 4 — Research Engine

Implement:

```text
features
factors
labels
datasets
statistics
backtest integration
experiment tracking
```

Build one complete research workflow end-to-end.

---

## PHASE 5 — Backtesting

Build a deterministic backtest engine.

First prove:

```text
data → strategy → signal → portfolio → P&L
```

Then add:

```text
costs
slippage
latency
partial fills
liquidity
```

---

## PHASE 6 — Risk Engine

Implement risk firewall before live execution.

---

## PHASE 7 — Paper Trading

Connect the broker abstraction to paper/simulation mode.

---

## PHASE 8 — Broker Integration

Implement OpenAlgo/Zerodha adapter only after:

```text
backtest PASS
risk PASS
paper PASS
reconciliation PASS
```

---

## PHASE 9 — AI Research Layer

Add:

```text
research agent
hypothesis generation
experiment creation
model critique
research memory
```

Do not begin with autonomous live trading.

---

## PHASE 10 — Live Trading

Only after all safety gates are operational.

---

# 32. FIRST STRATEGY FOR VALIDATION

Do NOT start by building a complex AI strategy.

Build one deterministic strategy first.

Example:

```text
Cross-sectional momentum
```

with:

```text
Universe
Feature
Signal
Ranking
Portfolio construction
Risk limits
Transaction costs
Backtest
Performance attribution
```

The purpose is validating the architecture, not maximizing returns.

---

# 33. FIRST END-TO-END DEMONSTRATION

The first milestone is:

```text
Historical NSE dataset
       ↓
Data validation
       ↓
Feature calculation
       ↓
Momentum alpha
       ↓
Portfolio construction
       ↓
Risk engine
       ↓
Backtest
       ↓
Transaction costs
       ↓
Performance report
       ↓
Experiment registered
```

If this works reproducibly, the architecture has a foundation.

---

# 34. CODING AGENT RULES

Cursor MUST:

1. Read the relevant architecture documents before modifying core code.
2. Search the reference repositories before implementing unfamiliar infrastructure.
3. Prefer small composable modules.
4. Avoid circular dependencies.
5. Keep domain logic independent of infrastructure.
6. Use dependency inversion for providers/brokers.
7. Write tests with implementation.
8. Never silently change architecture.
9. Document significant architecture decisions.
10. Never hardcode credentials.
11. Never introduce live trading accidentally.
12. Never bypass risk controls.
13. Never treat AI output as deterministic truth.
14. Never introduce look-ahead leakage intentionally or accidentally.
15. Never optimize solely for backtest Sharpe.
16. Prefer correctness over premature performance.
17. Prefer explicit types and contracts.
18. Maintain reproducibility.
19. Preserve auditability.
20. Fail safely.

---

# 35. CODE QUALITY

Target:

```text
Python 3.12+
Type hints
Ruff
Pytest
Pydantic
Structured logging
Docstrings for public interfaces
Small functions
Explicit interfaces
Dependency injection where useful
Deterministic tests
```

Avoid:

```text
god classes
global mutable state
hidden singleton brokers
business logic in API routes
business logic in UI
provider-specific types leaking everywhere
LLM-generated magic
untracked experiments
```

---

# 36. REFERENCE CODE POLICY

The agent may inspect reference repositories for understanding.

The agent MUST NOT:

- copy entire modules;
- copy large sections of code;
- reproduce proprietary implementation;
- remove licenses from copied code;
- present third-party code as original;
- mechanically fork/rebrand a project.

When an implementation pattern is useful:

```text
Study
 ↓
Understand
 ↓
Document principle
 ↓
Design QUANT LAB interface
 ↓
Implement independently
 ↓
Test
```

If an external dependency is appropriate, add it explicitly and respect its license.

---

# 37. ARCHITECTURE DECISION RECORDS

For major decisions create ADRs under:

```text
docs/decisions/
```

Examples:

```text
ADR-001-monorepo-architecture.md
ADR-002-data-provider-abstraction.md
ADR-003-event-engine.md
ADR-004-point-in-time-data.md
ADR-005-backtest-engine.md
ADR-006-risk-firewall.md
ADR-007-broker-abstraction.md
ADR-008-ai-permission-model.md
ADR-009-experiment-ledger.md
```

Each ADR:

```text
Context
Problem
Options
Decision
Consequences
References
```

---

# 38. REPOSITORY COMPARISON MATRIX

Create a table with:

| Capability | OpenBB | Qlib | VN.Py | Hummingbot | StockSharp | OpenAlgo | QuantDinger | Lumibot | TradingAgents |
|---|---|---|---|---|---|---|---|---|---|
| Data | | | | | | | | | |
| Features | | | | | | | | | |
| ML | | | | | | | | | |
| Backtest | | | | | | | | | |
| Portfolio | | | | | | | | | |
| Risk | | | | | | | | | |
| Execution | | | | | | | | | |
| Broker abstraction | | | | | | | | | |
| Event engine | | | | | | | | | |
| AI agents | | | | | | | | | |
| Experiment tracking | | | | | | | | | |
| Observability | | | | | | | | | |
| Local-first | | | | | | | | | |

Populate this from source inspection.

---

# 39. FINAL DESIGN PRINCIPLE

QUANT LAB should combine the best architectural ideas from the ecosystem:

```text
Qlib
    → quantitative research architecture

OpenBB
    → provider/data architecture

VN.Py
    → event-driven trading architecture

Hummingbot
    → execution architecture

StockSharp
    → comprehensive trading-domain modeling

OpenAlgo
    → Indian broker/execution abstraction

QuantDinger
    → modern operational architecture

Lumibot
    → backtest/paper/live strategy abstraction

TradingAgents
    → multi-agent research organization

Stefan Jansen / financial ML
    → rigorous research methodology
```

But QUANT LAB's differentiator must be:

```text
                 QUANT LAB
                     │
       ┌─────────────┼─────────────┐
       │             │             │
   Quant Math     Research       AI
       │             │             │
       └─────────────┼─────────────┘
                     │
              Research Integrity
                     │
              Portfolio + Risk
                     │
               Execution
                     │
              Broker / Market
```

The system must be designed like a **scientific computing laboratory connected to a trading execution system**, not like a chatbot connected to a broker.

---

# 40. IMMEDIATE COMMAND TO CURSOR

After reading this document, execute the following sequence.

### STEP 1

Inspect the existing workspace.

Report:

```text
Current files
Existing architecture
Existing dependencies
Existing code
Existing tests
Potential conflicts
```

Do not destroy existing work.

### STEP 2

Inspect all listed GitHub repositories.

Start with:

```text
Qlib
OpenBB
VN.Py
Hummingbot
StockSharp
OpenAlgo
QuantDinger
Lumibot
TradingAgents
```

Then inspect the remaining repositories.

### STEP 3

Create:

```text
docs/reference/REPOSITORY_STUDY.md
docs/reference/ARCHITECTURE_DECISION_MATRIX.md
```

### STEP 4

Create:

```text
docs/architecture/QUANT_LAB_ARCHITECTURE.md
```

with:

```text
system context
component architecture
data flow
research flow
backtest flow
risk flow
execution flow
AI flow
deployment topology
```

### STEP 5

Create ADRs for the foundational decisions.

### STEP 6

Create the QUANT LAB package skeleton.

### STEP 7

Implement the canonical domain objects.

### STEP 8

Implement tests immediately.

### STEP 9

Build the smallest functioning vertical slice:

```text
Historical Data
 ↓
Feature
 ↓
Alpha
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

### STEP 10

Run:

```text
lint
type checking
unit tests
integration tests
vertical-slice test
```

Fix all errors before moving forward.

---

# 41. DEFINITION OF DONE — FIRST DEVELOPMENT DAY

At the end of today's development session, QUANT LAB does NOT need to have:

```text
AI autonomous trading
Live trading
Full UI
All broker integrations
All data providers
Deep learning
RL
Options engine
HFT
```

Instead, it MUST have:

```text
✓ Repository study initiated/completed
✓ Architecture documented
✓ Clean project skeleton
✓ Canonical domain model
✓ Provider abstraction
✓ Strategy abstraction
✓ Backtest abstraction
✓ Risk abstraction
✓ Experiment abstraction
✓ Test framework
✓ First deterministic vertical slice
✓ No live trading enabled
✓ No credentials committed
✓ Clear next-step backlog
```

---

# 42. OPERATING MODE FOR CURSOR

From this point onward, behave as the **principal software architect + senior quantitative developer** for QUANT LAB.

Do not merely generate code from user prompts.

Before implementing a major subsystem:

```text
UNDERSTAND
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
REPORT
```

When uncertain between two architectures:

1. inspect the reference implementations;
2. compare trade-offs;
3. prefer the architecture that maximizes:
   - correctness;
   - reproducibility;
   - modularity;
   - testability;
   - auditability;
   - research integrity;
   - execution safety;
   - long-term extensibility.

Do not choose based solely on ease of implementation.

---

# 43. FINAL DIRECTIVE

**START BUILDING QUANT LAB.**

Do not wait for additional instructions after completing the repository reconnaissance.

Proceed sequentially:

```text
REPOSITORY STUDY
      ↓
ARCHITECTURE
      ↓
SKELETON
      ↓
DOMAIN
      ↓
DATA
      ↓
RESEARCH
      ↓
BACKTEST
      ↓
RISK
      ↓
PAPER EXECUTION
      ↓
AI RESEARCH
      ↓
LIVE EXECUTION
```

Every stage must leave the codebase in a working state.

The objective is not to produce a large amount of code.

The objective is to create a **correct, extensible, scientifically rigorous quantitative trading system whose architecture can eventually support serious research and real-money execution.**

**QUANT LAB BUILD START: 2026-08-30**
