# NAYAK QUANT LAB

Private local-first quantitative research and trading laboratory for the Indian equity and derivatives market.

QUANT LAB is a **scientific computing laboratory connected to a trading execution system**. It is not a chatbot connected to a broker.

```
DATA → INTEGRITY → RESEARCH → ALPHA → MODEL → VALIDATION
    → PORTFOLIO → RISK AUTHORIZATION → EXECUTION → ATTRIBUTION
```

AI is an assisting intelligence layer. It cannot bypass the risk firewall, execution rules, or human authorization.

## Current status (Prompt 01–31 — 2026-08-31)

Implemented:

- Quantitative core (MarketState, integrity engine, genome, next-bar backtest, JSONL ledger)
- Desktop application (PySide6): launch window, navigation, dashboard, research/backtest, **Validation**, **Features**, **Alpha Lab**, **Portfolio Lab**, **Risk Lab**, **Market Lab**, **Adaptive Lab**, **Model Lab**, **Ensemble Lab**, **Execution Lab**, **Capital Lab**, **Paper OMS Lab**, **Monitoring Lab**, **TCA & Capacity Lab**, **Econometrics Lab**, **Validation & Certification Lab**, **Shadow Trading Lab**, **Safety & Control Lab**, **Certification & Promotion Lab**, **Real-Time Data Lab**, **Real-Time Decision Lab**, **Digital Twin / Shadow Lab**, **Operations Control Lab**, **Broker Gateway Lab**, **Research Control**, **Discovery Lab**, **Knowledge Lab**, logs, system health, **Data** catalog
- Point-in-time **data fabric**: raw checksums, Parquet, DuckDB `as_of` queries, research gate
- **Research-grade validation**: walk-forward, cost/parameter robustness, block bootstrap, FDR/FWER, research gate (synthetic cannot promote)
- **Feature & alpha engine**: versioned PIT features, forward labels, IC/quantiles/decay, alpha combinations (Prompt 05 remains the promotion gate)
- **Cross-sectional portfolio construction**: versioned ensembles, hard/soft constraints, PIT covariance, transparent baselines and staged min-var/ERC, existing next-bar engine (Prompt 07 / ADR-021)
- **Factor & research risk engine**: versioned factors, equal-weight-universe beta, PIT sample/EWMA/shrinkage covariance, exposures, stress (not forecasts); missing ≠ 0 (Prompt 08 / ADR-022)
- **Market regime & state engine**: cross-section `StateSnapshot`, PIT rule/HMM-filter/walk-forward detectors, transitions, durations; smoothing blocked for prediction (Prompt 09 / ADR-023)
- **Adaptive alpha engine**: prequential predict-then-update, static/rolling/EWMA/ensemble baselines, decay and drift diagnostics (Prompt 10 / ADR-024)
- **Statistical learning engine**: walk-forward OLS/ridge/lasso/Huber/trees/PCA/selection, baseline comparisons, leak FAILs (Prompt 11 / ADR-025)
- **Ensemble / meta-alpha engine**: PIT equal/static/corr/dynamic weighting, walk-forward stacking, leave-one-out, diversity; not a second portfolio engine (Prompt 12 / ADR-026)
- **Execution research engine**: PIT spread/slippage/impact/latency/participation overlays on existing portfolio targets; simulated fills are not broker fills (Prompt 13 / ADR-027)
- **Research control plane**: versioned hypotheses, frozen specs, recorded grids, family multiple testing, falsification, lineage; coordinates existing engines (Prompt 14 / ADR-028)
- **Alpha discovery**: typed expression AST, seeded genetic/symbolic search, complexity/novelty/falsification, family BH via Prompt 14; expressions are hypotheses (Prompt 15 / ADR-029)
- **Research memory / knowledge graph**: typed nodes and edges, immutable evidence, genealogy, claims, contradictions, snapshots; knowledge is not authority (Prompt 16 / ADR-030)
- **Capital allocation / investment decisions**: explicit capital accounting, risk budgets, constrained Kelly, vol targeting, abstention, immutable hashed decisions and target portfolios — not orders (Prompt 17 / ADR-031)
- **Paper OMS**: target → intent → plan → paper order → simulated fill → position/cash → reconciliation; Prompt 13 fills reused; live broker not connected (Prompt 18 / ADR-032)
- **Monitoring**: post-decision P&L, attribution, drift, and research feedback; not a second backtester; profit is not a claim (Prompt 19 / ADR-033)
- **Market data**: PIT `available_time <= as_of`, immutable raw checksums, historical security identity, sourced calendars; no invented NSE history (Prompt 20 / ADR-034)
- **TCA / capacity**: implementation shortfall, PIT calibration, policy-defined capacity; Prompt 13 models reused; synthetic volume is not NSE ADV (Prompt 21 / ADR-035)
- **Safety gateway**: G0–G15 live-boundary evaluation, hashed authorization, kill switches; G15 BLOCK; not a broker (Prompt 25 / ADR-039)
- **Ops control plane**: supervisor, doctor, checksummed backup/restore, clock/disk; not live (Prompt 26 / ADR-040)
- **Live-trading certification**: promotion/release-eligibility gate; CERTIFIED is not live (Prompt 27 / ADR-041)
- **Broker gateway**: read-only mock account snapshots and reconciliation; no order routing (Prompt 28 / ADR-042)
- **Real-time data gateway**: observe-only mock/replay adapters; frozen MarketState(T); not a second fabric (Prompt 29 / ADR-043)
- **Real-time decision engine**: snapshot → target portfolio; uncertified releases abstain; not an OMS (Prompt 30 / ADR-044)
- **Digital twin**: deterministic shadow/replay with simulated fills; zero broker write (Prompt 31 / ADR-045)
- Jobs run off the UI thread; live trading remains **disabled**
- Reproducible synthetic momentum slice from CLI or the Backtest Lab (via the fabric)

Not implemented (intentionally):

- Live trading, OpenAlgo/Zerodha, official NSE holiday file, licensed real market dump, cloud hosting, full CSCV PBO, calibrated market impact, NIFTY/index beta, PIT sector/cap/fundamentals, commercial QP solver, ADF unit-root library, RL/LLM traders

## Launch the desktop app

```bash
cd "NAYAK QUANT LAB"
python3 -m venv .venv
source .venv/bin/activate
make install
make desktop
```

Or `quantlab desktop`. See [docs/development/LOCAL_RUN.md](docs/development/LOCAL_RUN.md).

Copy `.env.example` to `.env`. Do not set `LIVE_TRADING=true`.

## Architecture

- [docs/architecture/QUANT_LAB_DESKTOP_ARCHITECTURE.md](docs/architecture/QUANT_LAB_DESKTOP_ARCHITECTURE.md)
- [docs/architecture/RESEARCH_VALIDATION_ENGINE.md](docs/architecture/RESEARCH_VALIDATION_ENGINE.md)
- [docs/architecture/FEATURE_ALPHA_ENGINE.md](docs/architecture/FEATURE_ALPHA_ENGINE.md)
- [docs/architecture/PORTFOLIO_CONSTRUCTION.md](docs/architecture/PORTFOLIO_CONSTRUCTION.md)
- [docs/architecture/FACTOR_ENGINE.md](docs/architecture/FACTOR_ENGINE.md)
- [docs/architecture/RISK_ENGINE.md](docs/architecture/RISK_ENGINE.md)
- [docs/architecture/MARKET_STATE.md](docs/architecture/MARKET_STATE.md)
- [docs/architecture/REGIME_ENGINE.md](docs/architecture/REGIME_ENGINE.md)
- [docs/architecture/ADAPTIVE_ALPHA_ARCHITECTURE.md](docs/architecture/ADAPTIVE_ALPHA_ARCHITECTURE.md)
- [docs/architecture/STATISTICAL_MODEL_ENGINE.md](docs/architecture/STATISTICAL_MODEL_ENGINE.md)
- [docs/architecture/EXECUTION_RESEARCH_ENGINE.md](docs/architecture/EXECUTION_RESEARCH_ENGINE.md)
- [docs/architecture/RESEARCH_ORCHESTRATION_ENGINE.md](docs/architecture/RESEARCH_ORCHESTRATION_ENGINE.md)
- [docs/architecture/KNOWLEDGE_GRAPH_ENGINE.md](docs/architecture/KNOWLEDGE_GRAPH_ENGINE.md)
- [docs/architecture/CAPITAL_ALLOCATION_ENGINE.md](docs/architecture/CAPITAL_ALLOCATION_ENGINE.md)
- [docs/architecture/LIVE_TRADING_SAFETY_GATEWAY.md](docs/architecture/LIVE_TRADING_SAFETY_GATEWAY.md)
- [docs/architecture/PRODUCTION_OPERATIONAL_CONTROL_PLANE.md](docs/architecture/PRODUCTION_OPERATIONAL_CONTROL_PLANE.md)
- [docs/architecture/LIVE_TRADING_CERTIFICATION.md](docs/architecture/LIVE_TRADING_CERTIFICATION.md)
- [docs/architecture/BROKER_GATEWAY.md](docs/architecture/BROKER_GATEWAY.md)
- [docs/architecture/REALTIME_MARKET_DATA.md](docs/architecture/REALTIME_MARKET_DATA.md)
- [docs/architecture/REALTIME_DECISION_ENGINE.md](docs/architecture/REALTIME_DECISION_ENGINE.md)
- [docs/architecture/DIGITAL_TWIN.md](docs/architecture/DIGITAL_TWIN.md)
- [docs/architecture/QUANT_LAB_TARGET_ARCHITECTURE_v0.2.md](docs/architecture/QUANT_LAB_TARGET_ARCHITECTURE_v0.2.md)
- [docs/architecture/QUANT_LAB_ARCHITECTURE.md](docs/architecture/QUANT_LAB_ARCHITECTURE.md)
- [docs/development/BACKTESTING_PROTOCOL.md](docs/development/BACKTESTING_PROTOCOL.md)
- [docs/BACKLOG.md](docs/BACKLOG.md)

## Safety

Live execution requires every gate in `quantlab.core.config.LiveSafetyGates` to pass. The default configuration fails closed. The desktop UI cannot place orders or bypass the firewall.
