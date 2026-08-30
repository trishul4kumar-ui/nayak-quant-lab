# Repository Study

Inspected 2026-08-30 from GitHub source trees, licenses, and module layouts.
**Policy:** extract architecture and failure modes. Do not copy code.

Sources: [Qlib](https://github.com/microsoft/qlib), [OpenBB](https://github.com/OpenBB-finance/OpenBB), [VN.Py](https://github.com/vnpy/vnpy), [Hummingbot](https://github.com/hummingbot/hummingbot), [StockSharp](https://github.com/StockSharp/StockSharp), [OpenAlgo](https://github.com/marketcalls/openalgo), [QuantDinger](https://github.com/OpenByteInc/QuantDinger), [Lumibot](https://github.com/lumiwealth/lumibot), [TradingAgents](https://github.com/TauricResearch/TradingAgents), plus secondary methodology repos listed in the master instruction.

---

## Qlib (microsoft/qlib) — MIT

**Purpose.** End-to-end quantitative investment research: data, features, models, backtest, workflow.

**Stack.** Python, expression-based feature engine (`qlib/data/ops.py`), dataset abstractions, MLflow-style experiment recorder (`qlib/workflow/recorder.py`, `expm.py`), YAML-driven `init()`.

**Directory architecture (source).**

```
qlib/
  data/          # provider, cache, dataset, PIT, ops, storage
  model/         # model interface
  workflow/      # experiment manager, recorder, online serving
  backtest/      # exchange sim, account, strategy execution
  strategy/
  contrib/       # models, strategies, reports
  rl/
```

**Core abstractions.** Data provider URI (local or NFS) vs consumer; `Dataset` with processors; `Model` fit/predict; `Recorder` for params/metrics/artifacts; nested config objects.

**Point-in-time.** First-class `qlib/data/pit.py` — QUANT LAB must treat PIT as a data contract, not an afterthought.

**Strengths.** Research workflow, feature expressions, experiment tracking, China A-share heritage (transferable to NSE with different calendar/corporate-action rules).

**Weaknesses.** Global `qlib.init()` and config singleton; NFS-era client/server; weak live-execution and Indian-broker story; look-ahead still possible if users misuse processors.

**Lesson.** Separate **dataset version + feature expression + model + recorder**. Do not mix vendor APIs into research objects. Keep a PIT calendar.

---

## OpenBB (OpenBB-finance/OpenBB) — AGPL-3.0

**Purpose.** “Connect once, consume everywhere” market-data platform: Python, REST, MCP, Excel/Workspace.

**Stack.** Python package `openbb_platform/` with `core`, `providers`, `extensions`, `obbject_extensions`.

**Architecture.** Provider adapters implement a standard fetch contract; extensions expose domain commands (`equity.price.historical`); results wrap as OBBject. Consumers never import vendor SDKs.

**Strengths.** Provider/consumer inversion; normalized output; extension registry; AI/MCP as a *surface*, not the core.

**Weaknesses.** Not a trading engine. No order lifecycle, risk firewall, or research integrity ledger. AGPL is incompatible with copying — QUANT LAB must reimplement the *idea*, not the package.

**Lesson.** Data providers are plugins behind a protocol. Research and execution never import Kite/OpenAlgo types.

---

## VN.Py / VeighNa (vnpy/vnpy) — MIT

**Purpose.** Event-driven trading OS with gateways, apps, and (v4) `vnpy.alpha` ML research.

**Source layout.**

```
vnpy/
  event/engine.py     # queue + timer + handler dispatch
  trader/             # MainEngine, gateway.py, object.py, engine.py
  alpha/              # dataset, model, strategy, lab (Qlib-inspired)
  chart/, rpc/
```

**Core objects (`trader/object.py`).** Tick, Bar, Order, Trade, Position, Account, Contract, Log — broker-neutral dataclasses.

**Gateway (`trader/gateway.py`).** Connect/subscribe/send/cancel/query; events published into the engine. Strategy code talks to MainEngine, not CTP.

**Event engine.** Single-threaded queue (plus timer). Simple, testable, fail-closed if the engine dies.

**Strengths.** Order/position domain; gateway inversion; modular apps; alpha lab inspired by Qlib without forking it.

**Weaknesses.** Desktop-centric; Indian brokers are not first-class; limited experiment ledger compared with Qlib; UI mixed with engine in practice.

**Lesson.** Event types + gateway ABC + MainEngine as the only trading façade. Strategies never hold broker clients.

---

## Hummingbot — Apache-2.0

**Purpose.** Connector-centric automated trading (CEX/DEX), with scripts, V2 controllers, and executors.

**Architecture.** Connector standardizes REST/WS; **strategy ≠ executor**. Executors own order lifecycle (position, DCA, TWAP, triple-barrier). Paper connector exists (`binance_paper_trade`). Encrypted keystore.

**Strengths.** Connector isolation; executor reuse; explicit paper vs live; order-state machines.

**Weaknesses.** Crypto-first; not a research/PIT/factor platform; HFT-oriented complexity we do not need on Day 1.

**Lesson.** Execution algorithms are a package below strategy. Paper is a first-class gateway, not a flag inside live code.

---

## StockSharp — Apache-2.0 (C#)

**Purpose.** Full trading-domain platform: instruments, market data, connectors, strategies, backtest, storage.

**Layout.** Modular C# projects (`Algo.*`, `Messages`, `BusinessEntities`, connectors). Heavy domain modeling (security, portfolio, order, candle).

**Lesson.** Invest in a rich **instrument** model (lot size, tick, expiry, exchange) even if Python. Do not use a string ticker as the domain root.

---

## OpenAlgo (marketcalls/openalgo)

**Purpose.** Unified Indian broker API: orders, quotes, paper/sandbox, analyzer.

**Source layout (main).** Flask `app.py`, `broker/` adapters, `restx_api`, `sandbox`, `websocket_proxy`, `audit`, `keys`, `csp.py`, `mcp`.

**Strengths.** One API over Zerodha and other Indian brokers; paper sandbox; security files (CSP, secrets baseline).

**Weaknesses.** Application, not a quant research OS. Broker logic lives in HTTP routes. Trust boundary is the OpenAlgo process.

**Lesson.** QUANT LAB talks to OpenAlgo as **one** `BrokerGateway` implementation. Never scatter Kite REST through strategies. Treat OpenAlgo as an untrusted network boundary (timeouts, idempotency, reconcile).

---

## QuantDinger (OpenByteInc/QuantDinger)

**Purpose.** Self-hosted “AI trading OS”: research → code → backtest → paper/live → monitoring.

**v5 architecture (README).** HTTP API does **not** own trading loops. Separate processes: trading worker, scheduler, Celery (finite jobs), migrations. PostgreSQL is durable state; Redis is cache vs job broker (separate instances). Optional Prometheus. Non-root, read-only root FS in production overlay.

**Lesson.** Process isolation; Postgres as source of truth; Redis never owns positions; live trading opt-in; audit + OpenAPI for high-risk routes.

---

## Lumibot (lumiwealth/lumibot)

**Purpose.** Strategy class that is the same in backtest, paper, and live via a broker interface.

**Lesson.** `Strategy` lifecycle (`on_start`, bar/event handlers, `on_stop`) must be mode-agnostic. Clock and fill model are injected.

---

## TradingAgents (TauricResearch/TradingAgents)

**Purpose.** Multi-agent LLM research: analysts, bull/bear debate, trader, risk, portfolio manager. LangGraph, checkpoints, decision log.

**Source.** `tradingagents/agents`, `graph`, `dataflows`, `llm_clients`. Explicit look-ahead filtering called out in v0.3.1 notes.

**Strengths.** Role decomposition, decision logs, checkpoint resume.

**Weaknesses.** LLM sampling is non-reproducible (their own README). Not a risk firewall. Easy to confuse “agent approved” with “risk approved”.

**Lesson.** Agents emit **research artifacts and hypotheses**, never orders. Persist decision logs. Do not use LLM output as a fill or a risk decision.

---

## Secondary methodology (not forked)

| Source | Use |
|---|---|
| Stefan Jansen *Machine Learning for Trading* | Feature/label design, walk-forward, leakage |
| financial-machine-learning / AI-for-Trading | Factor families, CV for finance |
| awesome-quant | Ecosystem index only |
| AKShare | China data API — pattern of vendor adapters, not Indian data |
| QuantDinger (dup) | Same as above |
| turbovec / crypto-arbitrage bots | Out of scope for Day 1 NSE cash/F&O |

---

## Common abstractions (consensus)

1. **Instrument** as a first-class identity (exchange + symbol + type), not a ticker string.
2. **Provider/Gateway inversion** — adapters at the edge.
3. **Event or bar clock** injected into strategy.
4. **Order state machine** richer than “sent/filled”.
5. **Paper as a gateway**, not a boolean inside live code.
6. **Experiment recorder** (Qlib) for research; **audit log** (QuantDinger) for execution.

## Conflicting decisions (we must choose)

| Topic | Conflict | QUANT LAB choice |
|---|---|---|
| Config | Qlib global singleton vs Pydantic settings | Pydantic settings; no process-global broker |
| Events | VN.Py queue vs Hummingbot async | In-process event bus now; workers later |
| Data | Qlib binary store vs OpenBB live fetch | Parquet/DuckDB for research; adapters for ingest |
| AI | TradingAgents as trader vs assistant | Assistant only; cannot submit live orders |
| Package layout | Many Python packages vs one | One `quantlab` package, modular internals (ADR-001) |
| Live default | Many tools can go live easily | Fail closed; `LIVE_TRADING=false` |

## Weaknesses we will not inherit

- Global mutable `init()` (Qlib)
- Strategy → broker SDK imports
- LLM as execution authority
- Redis as position source of truth
- Look-ahead via “as-of today” fundamentals
- Naïve `for day in data: portfolio += signal`
