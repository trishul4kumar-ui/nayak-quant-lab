# QUANT LAB — next-step backlog

Prompt 01 + 02 + 03 + 04 (PIT fabric) + 05 (research-grade validation) + 06 (feature & alpha engine) + 07 (cross-sectional portfolio construction) + 08 (quantitative risk & factor research) + 09 (market regime, state & temporal dynamics) + 10 (adaptive alpha & online learning) + 11 (statistical learning & model research) + 12 (advanced ensemble, meta-alpha & model combination) + 13 (execution research / microstructure simulation) + 14 (research orchestration / control plane) + 15 (alpha discovery / genetic-symbolic search) + 16 (knowledge graph / research memory) + 17 (capital allocation / investment decision engine) + 18 (institutional paper OMS) + **19 (portfolio monitoring / attribution)** + **20 (production market data)** + **21 (TCA / calibration / capacity)** + **22 (econometric / causal research)** + **23 (model-risk validation / pre-live certification)** + **24 (production paper / shadow execution)** + **25 (live-trading safety gateway)** + **26 (production operational control plane)** + **27 (live-trading certification / promotion / release gate)** + **28 (broker abstraction / account reconciliation gateway)** + **29 (real-time market data / state gateway)** + **30 (real-time research-to-decision engine)** + **31 (deterministic shadow validation / replay / digital twin)**.

## Phase 3 — Data fabric
- [x] Parquet store + dataset versioning (DuckDB PIT queries, SQLite catalog)
- [x] Trading calendar abstraction (weekday IST; not official NSE holidays)
- [x] Corporate-action model + explicit split policy (synthetic fixture)
- [x] CSV ingest path for a user-supplied real dump (`quantlab data ingest`)
- [x] Universe membership `as_of(t)` architecture
- [ ] Official sourced NSE holiday file (user-provided; not invented here)
- [ ] Licensed real NSE/BSE historical dump
- [ ] Index membership product (NIFTY 50 history)

## Phase 4 — Research engine
- [x] Feature on MarketState + SignalGenome AST
- [x] Versioned feature/label/alpha engine (IC, quantiles, decay; not an indicator zoo)
- [x] Cross-sectional ensembles + constrained target portfolios (Prompt 07; optimizer does not invent alpha)
- [x] Factor library architecture + EW-universe beta + PIT covariance estimators (Prompt 08; NIFTY/cap/sector stay NOT_TESTED)
- [x] Cross-section StateSnapshot + PIT regime detectors (Prompt 09; NIFTY/ADV/ADF stay NOT_TESTED; HMM smoothing blocked for prediction)
- [x] Prequential adaptive learners + static/EWMA/ensemble baselines (Prompt 10; RL/LLM traders not built)
- [x] Statistical learning walk-forward (OLS/ridge/lasso/Huber/trees/PCA/selection; Prompt 11; not AutoML)
- [x] Combination ensembles + meta-alpha + walk-forward stacking (Prompt 12; not a second portfolio engine)
- [x] Execution-research simulation around existing targets (Prompt 13; not a second backtester; not OMS live)
- [x] Research control plane (Prompt 14; coordinates existing engines; no second gate or ledger)
- [x] Alpha discovery engine (Prompt 15; typed AST + frozen genetic search; not a second gate or ledger)
- [x] Knowledge graph / research memory (Prompt 16; immutable evidence; not a second gate or ledger)
- [x] Capital allocation / investment decision engine (Prompt 17; targets not orders; not a second portfolio engine)
- [x] Paper OMS / order lifecycle + paper accounting + reconciliation (Prompt 18; simulated fills only; not a live broker)
- [x] Portfolio monitoring / performance attribution / research feedback (Prompt 19; not a second backtester)
- [x] Production market-data provenance, security master, corporate actions, quality, snapshots (Prompt 20; no invented NSE history)
- [x] TCA / execution calibration / policy-defined capacity (Prompt 21; Prompt 13 reused; not live)
- [x] Econometric / causal research engine (Prompt 22; Granger is predictive; Johansen/PP remain NOT_TESTED)
- [x] Model-risk independent validation / pre-live certification (Prompt 23; CERTIFIED is not live)
- [x] Production paper trading / shadow execution engine (Prompt 24; not live, not a broker)
- [x] Live-trading safety gateway (Prompt 25; G15 BLOCK; not a broker)
- [x] Production operational control plane (Prompt 26; doctor/backup/supervisor; not live)
- [x] Live-trading certification / promotion / release gate (Prompt 27; CERTIFIED ≠ LIVE; not a broker)
- [x] Broker abstraction / account reconciliation gateway (Prompt 28; read-only mock; no order routing)
- [x] Real-time market-data / state gateway (Prompt 29; observe-only mock/replay; not a second fabric)
- [x] Real-time research-to-decision engine (Prompt 30; TargetPortfolio is not an order)
- [x] Deterministic shadow validation / replay / digital twin (Prompt 31; zero broker write; not Prompt 24)
- [x] Integrity engine PASS/WARN/FAIL/NOT_TESTED
- [x] Walk-forward splitter (rolling / expanding / anchored)
- [x] Multiple-testing FDR/FWER available (BH, Bonferroni, Holm)
- [x] Research gate (no live promotion; synthetic cannot promote)
- [ ] Full combinatorial PBO / CSCV
- [x] Calibrated market-impact / ADV participation architecture (Prompt 21; coefficients remain uncalibrated / NOT_TESTED vs NSE)
- [ ] Official-index (NIFTY) beta and PIT sector/cap/fundamentals

## Phase 5 — Backtester
- [x] Pluggable slippage interface (none / fixed bps / spread / volume-participation unevaluable)
- [x] Research-layer participation, partial fills, latency (Prompt 13; canonical `run_backtest` remains next-bar)
- [ ] Order queue inside `run_backtest`
- [ ] NSE auction / circuit-breaker hooks (model, not live)

## Phase 6 — Risk
- [x] HALT/EMERGENCY fail closed
- [ ] Drawdown halt, daily loss, sector exposure
- [ ] Liquidity ADV check (architecture present; data not bundled)

## Phase 7 — Paper
- [x] Paper OMS matching order lifecycle states (Prompt 18; paper only)
- [x] Reconciliation interface (paper vs internal)
- [x] Post-decision monitoring / attribution (Prompt 19)

## Phase 8 — Brokers
- [ ] OpenAlgo adapter (only after paper + reconcile tests)
- [ ] Zerodha via OpenAlgo, not Kite in strategy code

## Phase 9 — AI research
- [x] Expanded permission model (`OVERRIDE_RESEARCH_GATE` denied)
- [ ] Permissioned tools: read experiments, propose hypotheses
- [ ] Critic agent that cannot mark alpha “valid”

## Phase 10 — Live
- [x] All safety gates + session + human dual-control architecture (Prompt 25; live still disabled)

## Desktop (Prompt 03)
- [x] PySide6 main window, health, jobs, backtest from UI, log viewer
- [x] Validation page (client of `quantlab.app`; not run on every Backtest click)
- [x] Features + Alpha Lab viewers (definitions and ledger IC; UI does not compute features)
- [x] Portfolio Lab viewer (seed constructors and last ledger experiment; UI does not compute weights)
- [x] Risk Lab viewer (factor catalog and last factor/risk experiment; UI does not compute covariance)
- [x] Market Lab viewer (CS snapshot and regime catalog; UI does not fit HMM)
- [x] Adaptive Lab viewer (learner catalog and last adaptive experiment; UI does not fit models)
- [x] Model Lab viewer (statistical-model catalog and last model experiment; UI does not fit models)
- [x] Ensemble Lab viewer (combination catalog and last combination experiment; UI does not fit ensembles)
- [x] Execution Lab viewer (microstructure catalog and last execution experiment; UI does not simulate fills)
- [x] Research Control viewer (hypotheses and last orchestration experiment; UI does not run grids)
- [x] Discovery Lab viewer (families and last discovery search; UI does not evaluate expressions)
- [x] Knowledge Lab viewer (nodes, edges, last snapshot; UI does not parse Parquet or write the ledger)
- [x] Capital Lab viewer (policies and last decision; UI does not compute allocations or write the ledger)
- [x] Paper OMS Lab viewer (policies and last paper run; SUBMIT PAPER is local simulation only)
- [x] Monitoring Lab viewer (last performance/attribution; UI does not compute P&L)
- [x] TCA & Capacity Lab viewer (shortfall/capacity; UI does not calibrate or route)
- [x] Econometrics Lab viewer (stationarity/Granger; UI does not fit models)
- [x] Validation & Certification Lab viewer (checklist/state; UI cannot force CERTIFIED or live)
- [x] Shadow Trading Lab viewer (cycles/badges; RUN SHADOW is local only; no broker routing)
- [x] Safety & Control Lab viewer (G0–G15; RUN SAFETY is local only; LIVE DISABLED)
- [x] Operations Control Lab viewer (doctor/health; RUN DOCTOR is local only; no secrets)
- [x] Certification & Promotion Lab viewer (criteria/state; RUN CERTIFICATION is local only; not live)
- [x] Broker Gateway Lab viewer (read-only snapshot; RUN SNAPSHOT is local mock; no order routing)
- [x] Real-Time Data Lab viewer (observe-only snapshot; RUN SNAPSHOT is local mock; no streams)
- [x] Real-Time Decision Lab viewer (RUN DECISION is local; no order controls)
- [x] Digital Twin / Shadow Lab viewer (RUN SHADOW is local; zero broker write)
- [ ] Saved docking layouts
- [ ] PyInstaller signed installer
- [ ] Resource monitor
