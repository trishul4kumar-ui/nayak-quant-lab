# QUANT LAB Architecture Reconciliation

**Date:** 2026-08-30  
**Inputs:** Prompt 01 workspace, Prompt 02 directive, repository study, existing ADRs.

Prompt 01 produced a working research core. Prompt 02 does **not** replace it. This document records KEEP / CHANGE / ADD / REMOVE / DEFER.

## What Prompt 01 created (keep)

| Artifact | Status |
|---|---|
| `src/quantlab` single package (ADR-001) | KEEP |
| Provider protocol + synthetic NSE bars | KEEP |
| PIT timestamps on bars (ADR-004) | KEEP |
| Next-bar backtest (ADR-005) | KEEP |
| RiskFirewall.authorize (ADR-006) | KEEP |
| Paper gateway; OpenAlgo stub disabled | KEEP |
| Experiment JSONL ledger | KEEP |
| LIVE_TRADING fail-closed | KEEP |
| Cross-sectional momentum as architecture test | KEEP |
| AI cannot request live orders | KEEP |

## Conflicts with Prompt 02

| Topic | Prompt 01 | Prompt 02 | Decision |
|---|---|---|---|
| Integrity report | `dict[str, bool]` | PASS / WARN / FAIL / NOT_TESTED | **CHANGE** to enum strings |
| Order states | no RISK_PENDING | VALIDATING → RISK_PENDING → APPROVED | **ADD** RISK_PENDING |
| Strategy input | raw OHLCV in context | MarketState first | **ADD** MarketState; bars remain for PIT |
| Metrics | return + drawdown | CAGR, Sharpe, Sortino, Calmar, win rate, … | **ADD** mathcore metrics |
| Signal object | score + instrument | SignalGenome AST | **ADD** genome; Signal remains the evaluated output |
| Integrity engine | four boolean flags | dedicated engine | **ADD** `research.integrity` |
| AI capabilities | smaller set | CREATE_HYPOTHESIS, CREATE_FEATURE, … | **CHANGE** expand enum; live still denied |
| Experiment fields | subset | hypothesis_id, lineage, cost/slippage/latency models | **ADD** optional fields |
| UI / desktop | not built | Prompt 03 exists on disk | **DEFER** (not this prompt) |

No useful Prompt 01 code is removed.

## KEEP

- Monorepo as one Python package
- Domain objects for Instrument, Bar, Order, Fill, Position, Portfolio, Signal, Experiment
- Broker-neutral strategy protocol
- Event bus (in-process)
- Paper ≠ live
- numpy/pandas already listed; used now for the math core

## CHANGE

- Experiment and backtest integrity payloads use `pass|warn|fail|not_tested`
- Risk firewall carries an explicit `RiskState` (default NORMAL)
- StrategyContext may carry `market_states` in addition to bars
- AI permission names aligned with Prompt 02 (`READ_MARKET_DATA`, `CREATE_HYPOTHESIS`, …) while keeping live-order denial

## ADD

- MarketState + builder
- SignalGenome (schema + eval; genetic search lives in `quantlab.discovery`, not here)
- Discovery ExprNode + bounded genetic/symbolic search (Prompt 15)
- Knowledge graph / research memory (Prompt 16; typed adjacency, not a graph database)
- ResearchHypothesis, Alpha, research status machine
- Data lineage object
- Research integrity engine
- Mathematical primitives (returns, z-score, Sharpe, …)
- Portfolio optimizer protocol (equal-weight / top-N rank)
- Model lifecycle enum + Predictor protocol (no neural nets)
- Reconciliation engine interface (paper vs internal)
- Risk states HALT/EMERGENCY fail closed
- Baseline strategies: buy-and-hold, equal-weight, seeded random
- License/concept mapping document
- Target architecture v0.2
- Walk-forward, purge/embargo, research gate (Prompt 05 / ADR-019)
- Feature/label/alpha engine with hashed identity (Prompt 06 / ADR-020)
- Cross-sectional ensembles and constrained portfolio construction (Prompt 07 / ADR-021)
- Factor engine + research risk model (Prompt 08 / ADR-022); EW-universe beta, not NIFTY
- Market regime / CS state engine (Prompt 09 / ADR-023); filtered ≠ smoothed; not NIFTY
- Adaptive alpha / prequential learners (Prompt 10 / ADR-024); not a live agent
- Statistical learning walk-forward (Prompt 11 / ADR-025); numpy estimators; not AutoML; ledger stays in `quantlab.models`
- Combination / meta-alpha engine (Prompt 12 / ADR-026); PIT weighting and stacking; Prompt 07 `research ensemble` unchanged
- Execution research engine (Prompt 13 / ADR-027); simulated fills around existing targets; OMS live path unchanged
- Knowledge graph / research memory (Prompt 16 / ADR-030); typed adjacency, not a graph database
- Capital allocation / investment decision engine (Prompt 17 / ADR-031); target portfolios, not orders; Prompt 07 `research portfolio` unchanged
- Paper OMS (Prompt 18 / ADR-032); paper orders/fills/accounting/reconciliation; Prompt 13 fills reused; live broker not connected
- Block bootstrap, sign-flip null, BH/Bonferroni/Holm, deflated Sharpe architecture

## REMOVE

- Nothing of Prompt 01’s public contracts except the boolean integrity map (migrated)

## DEFER (explicit)

- Unrestricted / unbounded genetic programming (Prompt 15 is a bounded seeded search in `quantlab.discovery`)
- Kalman / RL / HFT / options / LLM traders (HMM exists as a filtered research detector; IC-gated adaptive learners exist; smoothing is not a trading feature)
- Official NSE holiday file / licensed dump / NIFTY history
- Full combinatorial PBO / CSCV
- Calibrated market impact
- Official-index (NIFTY) beta / licensed dump / PIT sector-cap-fundamentals
- OpenAlgo/Zerodha live adapters
- Multi-agent AI orchestration (distinct from Prompt 14 research control plane)
- Cloud
