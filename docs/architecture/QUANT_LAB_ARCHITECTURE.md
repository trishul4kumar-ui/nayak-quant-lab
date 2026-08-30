# QUANT LAB Architecture

**Status:** accepted (Prompts 19–24: ADR-033 … ADR-038)  
**Code root:** `src/quantlab` (see ADR-001)

## System context

QUANT LAB is a local-first research and (later) execution OS for Indian cash and derivatives. Users are quantitative researchers. Brokers and data vendors sit behind adapters. AI assistants read research state and write hypotheses; they cannot open live orders.

```
[Researcher / notebooks / CLI]
        │
        ▼
┌───────────────────────────────────────┐
│              QUANT LAB                 │
│  domain │ data │ research │ portfolio   │
│  risk   │ backtest │ execution │ brokers │
│  ai (assist) │ observability              │
└───────────────────────────────────────┘
        │                    │
        ▼                    ▼
  Parquet / DuckDB      Postgres (ops, later)
  Experiment ledger     Redis cache (never SoT)
        │
        ▼
  OpenAlgo / Zerodha / Paper   (adapters only)
```

## Component architecture

| Package | Responsibility | May depend on |
|---|---|---|
| `core` | Config, clock, IDs, errors, events, logging | — |
| `domain` | Canonical objects | core |
| `data` | PIT fabric, provenance, security master, corporate actions, quality, snapshots | core, domain |
| `features` | Versioned PIT feature definitions and engine | core, domain, data |
| `labels` | Forward labels only | core, domain, features |
| `alpha` | Alpha objects, IC/quantiles, experiment pipeline | core, domain, features, labels, research |
| `factors` | Versioned PIT factors, EW-universe beta, exposures | core, domain, features, alpha.combinations |
| `regimes` | CS StateSnapshot, PIT detectors, transitions | core, domain, features, factors.market |
| `adaptive` | Prequential learners, decay, drift, ensemble weights | core, domain, features, alpha, regimes |
| `learning` | Walk-forward statistical models (not AutoML, not the ledger) | core, domain, features, labels, alpha, regimes, adaptive.decay |
| `ensemble` | PIT combination / meta-alpha / stacking (not a portfolio engine) | core, domain, features, alpha, learning, adaptive, factors, regimes |
| `execution_research` | PIT microstructure, simulated fills, capacity (not OMS, not a second backtester) | core, domain, backtest.costs, portfolio.construction, research.momentum |
| `orchestration` | Research control plane: hypotheses, families, recorded grids, lineage (not a second gate) | core, domain, research, existing engines via runner |
| `discovery` | Typed expression search, genetic/symbolic discovery, novelty (not a second gate or alpha) | core, domain, features, labels, alpha.ic, research.gate, orchestration.multiple_testing |
| `knowledge` | Research memory, genealogy, evidence, claims, snapshots (not a second gate or ledger) | core, domain, discovery.expression, orchestration.report (ingest only) |
| `capital` | Capital allocation, investment decisions, target portfolios (not orders, not a second covariance/portfolio engine) | core, domain, portfolio.optimize/risk_model/turnover, research.gate, research.integrity |
| `paper_oms` | Paper order lifecycle, simulated fills, paper accounting, reconciliation (not a second backtester, not a live broker) | core, domain, capital.definitions, execution_research.fills/scenarios, research.integrity, risk.firewall |
| `monitoring` | Post-decision performance, attribution, drift, research feedback (not a second backtester) | core, domain, capital.definitions, paper_oms, research.integrity |
| `tca` | Implementation shortfall, PIT calibration, policy capacity, fragility (wraps Prompt 13; not a second simulator) | core, domain, execution_research, paper_oms, research.integrity |
| `econometrics` | Stationarity, cointegration, VAR/VECM, Granger, breaks, panel, causal diagnostics (not a second backtester or gate) | core, domain, research.integrity, research.multiple_testing, execution_research.costs |
| `certification` | Model-risk independent validation and pre-live certification (governance, not live) | core, domain, paper_oms, tca, monitoring, econometrics, research.integrity |
| `shadow` | Production paper/shadow cycles wrapping paper OMS (not live, not a broker, not a second OMS) | core, domain, paper_oms, data.fabric.calendar, certification, research.integrity |
| `safety` | Live-trading safety gateway G0–G15 (not a broker, not live) | core, domain, research.integrity |
| `ops` | Production operational control plane (not live, not a broker) | core, domain, research.integrity |
| `release` | Live-trading certification / promotion / release eligibility (not live, not Prompt 23) | core, domain, safety, ops, research.integrity |
| `broker_gateway` | Read-only broker/account snapshots and reconciliation (not order routing) | core, domain, research.integrity |
| `realtime_data` | Observe-only real-time market-data gateway (not a second fabric, not a broker) | core, domain, data.fabric.calendar, research.integrity |
| `realtime_decision` | Production-time decision cycle; TargetPortfolio is terminal (not an OMS) | core, domain, capital.definitions, realtime_data, research.integrity |
| `digital_twin` | Deterministic shadow/replay twin (not Prompt 24, not a broker) | core, domain, realtime_data, realtime_decision, research.integrity |
| `research` | Genome, momentum strategy, validation suite, gate | core, domain, data |
| `models` | Experiment ledger + Predictor protocol | core, domain |
| `portfolio` | Signal → target positions; CS constructors | core, domain, features, alpha, backtest (experiment only) |
| `risk` | Firewall (`__init__`); research cov/stress/experiment modules | core, domain, portfolio.covariance, factors (experiment only) |
| `backtest` | Event/bar simulator, costs, metrics | core, domain, portfolio, risk |
| `execution` | OMS state machine | core, domain, risk |
| `brokers` | `BrokerGateway` + paper | core, domain |
| `ai` | Permissions only (Day 1) | core |
| `observability` | Structured logs, audit sink | core |

**Forbidden:** `research` → `brokers`; `ai` → `execution.submit` for live; API routes containing sizing logic.

## Data flow

```
Vendor / file / synthetic
    → MarketDataProvider
    → normalize (InstrumentId, INR, Asia/Kolkata session)
    → validate (OHLC, monotonic time, PIT fields)
    → store (in-memory Day 1; Parquet later)
    → Dataset (universe + interval + version)
```

Every bar carries `event_time`, `effective_time`, `available_time`, `ingestion_time`.

## Research flow

```
Hypothesis → Feature definition → Label (explicit horizon)
    → Dataset as-of T
    → Integrity checks (leakage, survivorship flags)
    → Alpha / model
    → ExperimentRun metadata
```

## Backtest flow (Day 1 vertical slice)

```
Dataset
  → Cross-sectional momentum feature (lookback N)
  → Rank → equal-weight top-K (signal ≠ order)
  → RiskFirewall on target weights
  → Next-bar open-to-open or close-to-close return
  → Proportional transaction costs on turnover
  → Metrics + ExperimentLedger.append
```

Signal at bar `t` earns the return from `t` to `t+1` (no same-bar fill).

## Risk flow

```
ProposedPortfolio
  → instrument listed?
  → position / name count limits
  → gross / net exposure
  → (later) liquidity, loss, volatility, broker rules
  → RiskDecision {APPROVE, MODIFY, REJECT}
```

Logged. No caller may skip `RiskFirewall.authorize`.

## Paper OMS flow (Prompt 18)

```
TargetPortfolio → OrderIntent → OrderPlan → PaperOrder
  → PaperExecutionAdapter.simulate (Prompt 13 fills)
  → PaperFill → Position / Cash → ReconciliationReport
```

Live broker is not connected. `quantlab.execution.ExecutionEngine` remains the live façade and still cannot place live orders.

## Monitoring flow (Prompt 19)

```
Paper positions / cash → PerformanceSnapshot → Attribution → Drift / Risk
  → ResearchFeedback → Knowledge Graph
```

Not a second backtester. Profit is not a claim.

## TCA flow (Prompt 21)

```
Paper fills → Arrival benchmark → Implementation shortfall
  → optional PIT calibration (freeze) → policy capacity → fragility
```

Prompt 13 models are reused. Observed ≠ modelled. Synthetic volume ≠ NSE ADV.

## AI flow

```
READ_DATA / WRITE_RESEARCH / RUN_EXPERIMENT / RUN_BACKTEST
```

`REQUEST_LIVE_ORDER` is defined and **denied** for all agents. Deterministic risk + human gates only.

## Deployment topology (target)

```
research host (this repo)
  apps/research  notebooks + CLI
  apps/api        later
  apps/trading    worker later (QuantDinger-style, not in API process)
  postgres / redis via docker-compose (optional Day 1)
```

Day 1 runs in-process with an on-disk JSONL experiment ledger.

Prompt 02 target architecture: [`QUANT_LAB_TARGET_ARCHITECTURE_v0.2.md`](QUANT_LAB_TARGET_ARCHITECTURE_v0.2.md). Reconciliation: [`QUANT_LAB_ARCHITECTURE_RECONCILIATION.md`](QUANT_LAB_ARCHITECTURE_RECONCILIATION.md). Desktop shell: [`QUANT_LAB_DESKTOP_ARCHITECTURE.md`](QUANT_LAB_DESKTOP_ARCHITECTURE.md). Validation: [`RESEARCH_VALIDATION_ENGINE.md`](RESEARCH_VALIDATION_ENGINE.md). Features/alpha: [`FEATURE_ALPHA_ENGINE.md`](FEATURE_ALPHA_ENGINE.md). Portfolio: [`PORTFOLIO_CONSTRUCTION.md`](PORTFOLIO_CONSTRUCTION.md). Factors: [`FACTOR_ENGINE.md`](FACTOR_ENGINE.md). Market state: [`MARKET_STATE.md`](MARKET_STATE.md). Regimes: [`REGIME_ENGINE.md`](REGIME_ENGINE.md). Adaptive: [`ADAPTIVE_ALPHA_ARCHITECTURE.md`](ADAPTIVE_ALPHA_ARCHITECTURE.md). Statistical models: [`STATISTICAL_MODEL_ENGINE.md`](STATISTICAL_MODEL_ENGINE.md). Execution research: [`EXECUTION_RESEARCH_ENGINE.md`](EXECUTION_RESEARCH_ENGINE.md). Orchestration: [`RESEARCH_ORCHESTRATION_ENGINE.md`](RESEARCH_ORCHESTRATION_ENGINE.md). Knowledge: [`KNOWLEDGE_GRAPH_ENGINE.md`](KNOWLEDGE_GRAPH_ENGINE.md). Capital: [`CAPITAL_ALLOCATION_ENGINE.md`](CAPITAL_ALLOCATION_ENGINE.md). Paper OMS: [`PAPER_OMS_ARCHITECTURE.md`](PAPER_OMS_ARCHITECTURE.md). Monitoring: [`PERFORMANCE_MONITORING_ENGINE.md`](PERFORMANCE_MONITORING_ENGINE.md). Market data: [`PRODUCTION_MARKET_DATA.md`](PRODUCTION_MARKET_DATA.md). TCA: [`../research/TCA_CALIBRATION_CAPACITY.md`](../research/TCA_CALIBRATION_CAPACITY.md). Safety gateway: [`LIVE_TRADING_SAFETY_GATEWAY.md`](LIVE_TRADING_SAFETY_GATEWAY.md). Ops: [`PRODUCTION_OPERATIONAL_CONTROL_PLANE.md`](PRODUCTION_OPERATIONAL_CONTROL_PLANE.md). Live certification: [`LIVE_TRADING_CERTIFICATION.md`](LIVE_TRADING_CERTIFICATION.md). Broker gateway: [`BROKER_GATEWAY.md`](BROKER_GATEWAY.md).

## Promotion path

`RESEARCH → BACKTEST → WALK-FORWARD / ROBUSTNESS / STATISTICS → RESEARCH CANDIDATE → PAPER → SHADOW → LIVE`

The codebase is on **RESEARCH/BACKTEST/PAPER/SHADOW**. The live-trading safety gateway (Prompt 25), ops control plane (Prompt 26), live-certification gate (Prompt 27), and read-only broker gateway (Prompt 28) are present; live vendor adapters and live order routing are not implemented. `LIVE_TRADING` remains false. `BROKER_WRITE_ENABLED` remains false.
