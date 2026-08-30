# QUANT LAB — PROMPT 19
# Institutional Portfolio Monitoring, Performance Attribution & Research Feedback Engine

**Target release:** QUANT LAB 1.9.0  
**Status:** Implementation specification  
**Depends on:** Prompts 01–18  
**Primary objective:** Build an institutional-grade post-decision monitoring, performance measurement, attribution, and research-feedback layer.

## 0. CODING-AGENT DIRECTIVE

You are modifying an existing QUANT LAB codebase. **Do not rewrite, fork, duplicate, or bypass existing engines.**

Before coding:

1. Inspect the complete existing repository.
2. Read Prompts 01–18 implementation, ADRs, architecture documents, tests, CLI registration, app services, UI navigation, ledger, and Knowledge Graph integration.
3. Produce a short implementation plan and dependency map.
4. Preserve all existing public interfaces unless a backward-compatible extension is required.
5. Reuse canonical engines rather than creating competing implementations.

**Never trade. Never import a broker into this package. Never enable live trading.**

## 1. CORE RESEARCH QUESTION

The engine must answer:

> **What actually happened to the portfolio after an investment decision, why did it happen, where did P&L and risk come from, how much differed from the intended portfolio, and what should the research system learn from the outcome?**

Performance is evidence about an executed/simulated portfolio, not proof of alpha.

## 2. NON-NEGOTIABLE ONTOLOGY

Do not collapse these concepts:

```text
ALPHA
≠ MODEL
≠ ENSEMBLE
≠ PORTFOLIO
≠ TARGET PORTFOLIO
≠ ORDER
≠ PAPER FILL
≠ POSITION
≠ PERFORMANCE
≠ ATTRIBUTION
≠ RISK
≠ RESEARCH EVIDENCE
≠ CLAIM
```

Performance attribution must explain outcomes; it must not retroactively alter the investment decision.

## 3. ARCHITECTURAL POSITION

```text
RESEARCH
  ↓
VALIDATION / GATE
  ↓
CAPITAL ALLOCATION
  ↓
TARGET PORTFOLIO
  ↓
PAPER OMS
  ↓
PAPER FILLS / POSITIONS
  ↓
PROMPT 19
  ├── PERFORMANCE
  ├── ATTRIBUTION
  ├── EXPOSURE
  ├── RISK MONITORING
  ├── DRIFT
  ├── BENCHMARK RELATIVE ANALYSIS
  └── RESEARCH FEEDBACK
          ↓
      KNOWLEDGE GRAPH
```

Prompt 19 is not a second backtester. It consumes canonical portfolio/position/fill observations.

## 4. REQUIRED PACKAGE

Create:

```text
src/quantlab/monitoring/
```

Suggested modules:

```text
models.py
performance.py
returns.py
pnl.py
attribution.py
risk_monitor.py
exposure.py
drift.py
benchmark.py
factor_attribution.py
alpha_attribution.py
drawdown.py
concentration.py
turnover.py
reconciliation.py
feedback.py
identity.py
integrity.py
repository.py
service.py
library.py
cli.py
errors.py
enums.py
__init__.py
```

Keep `__init__.py` thin.

Add corresponding:

```text
src/quantlab/app/monitoring.py
src/quantlab/ui/pages/monitoring_lab.py
tests/monitoring/
docs/architecture/PERFORMANCE_MONITORING_ENGINE.md
docs/architecture/ATTRIBUTION_ENGINE.md
docs/research/PERFORMANCE_RESEARCH.md
docs/research/RESEARCH_FEEDBACK.md
docs/decisions/ADR-033-portfolio-monitoring-attribution.md
```

## 5. PERFORMANCE MODEL

Implement explicit accounting identities.

At minimum:

```text
Equity_t = Cash_t + Σ(Position_i,t × Mark_i,t)

PnL_total = RealizedPnL + UnrealizedPnL + Income - Costs - Fees - Adjustments

NetReturn = NetPnL / AppropriateBeginningCapital
```

Never silently equate:

```text
capital = portfolio market value
```

Maintain explicit:

- beginning equity
- ending equity
- cash
- reserved cash
- gross exposure
- net exposure
- long exposure
- short exposure if supported
- realized P&L
- unrealized P&L
- transaction costs
- financing/borrow costs when available
- residual/unexplained P&L

Unknown components must remain `None` / `NOT_TESTED`, not zero.

## 6. RETURN ENGINE

Support:

- simple return
- log return
- cumulative return
- time-weighted return where valid
- money-weighted return where valid
- daily/session return
- rolling volatility
- rolling Sharpe with explicit risk-free assumption
- rolling drawdown
- recovery time
- downside deviation

Do not annualize without sufficient observations.

Default assumptions must be explicit and provenance-tagged.

## 7. SECURITY-LEVEL ATTRIBUTION

For each security:

- contribution to P&L
- contribution to return
- realized contribution
- unrealized contribution
- transaction-cost contribution
- turnover contribution
- drawdown contribution
- exposure contribution

Contributions must reconcile:

```text
Σ security contribution + residual = total portfolio result
```

Residual must be visible.

## 8. ALPHA ATTRIBUTION

Where lineage exists, attribute portfolio outcome to:

- alpha/expression
- model
- ensemble
- portfolio construction
- execution
- costs
- residual

Do not manufacture attribution where causal decomposition is unavailable.

Label decomposition as:

- exact accounting attribution
- model-based attribution
- estimated attribution
- unavailable

## 9. FACTOR / RISK ATTRIBUTION

Reuse Prompt 08 factor/risk infrastructure.

Support:

```text
Portfolio return ≈ factor contribution + residual
```

where valid.

Calculate:

- factor exposure
- factor contribution
- residual return
- residual volatility
- factor risk contribution
- concentration
- covariance contribution

Do not create a second covariance engine.

NIFTY, sector, market-cap, ADV and other unavailable inputs remain `NOT_TESTED`.

## 10. PORTFOLIO DRIFT

Compare:

```text
TargetPortfolio
        vs
Paper/Observed Portfolio
```

Measure:

- weight drift
- quantity drift
- cash drift
- exposure drift
- turnover
- implementation gap
- residual orders
- unfilled quantity
- execution deviation

Never silently rebalance.

## 11. BENCHMARKS

Implement benchmark interfaces without inventing NIFTY data.

Support:

- internal equal-weight universe benchmark
- user-supplied benchmark
- future NIFTY/index benchmark when valid PIT data exists

Clearly distinguish:

```text
BENCHMARK RELATIVE
vs
ABSOLUTE PERFORMANCE
```

No fabricated benchmark series.

## 12. DRAWDOWN / RISK MONITORING

Track:

- current drawdown
- maximum drawdown
- drawdown episodes
- duration
- recovery
- rolling volatility
- concentration
- gross/net exposure
- factor exposure
- turnover
- loss clusters

Reuse Prompt 05/08 risk concepts.

Monitoring must not silently change risk limits.

## 13. RESEARCH FEEDBACK

Create immutable feedback records:

```text
OBSERVATION
→ ATTRIBUTION
→ INTERPRETATION
→ RESEARCH QUESTION
```

Examples:

- alpha generated gross return but execution consumed the edge
- performance concentrated in one security
- factor exposure explained most apparent alpha
- portfolio construction reduced signal efficacy
- turnover dominated costs
- paper execution deviated materially from target

Feedback is not automatically a new hypothesis.

## 14. KNOWLEDGE GRAPH

Create/link nodes such as:

```text
PERFORMANCE_RUN
PERFORMANCE_OBSERVATION
ATTRIBUTION_RESULT
RISK_OBSERVATION
DRIFT_OBSERVATION
RESEARCH_FEEDBACK
```

Link to:

- investment decision
- target portfolio
- paper OMS run
- fills
- experiment
- alpha
- model
- factor
- knowledge claim

Failed or adverse outcomes must never be deleted.

## 15. LEDGER

Extend existing JSONL ledger backward-compatibly.

Possible fields:

```text
monitoring_run_id
performance_snapshot_id
performance_hash
attribution_hash
target_portfolio_hash
observed_portfolio_hash
benchmark_id
attribution_method
residual_pnl
research_feedback_id
```

No second ledger.

## 16. INTEGRITY

Add checks such as:

```text
future_performance_mark
future_attribution_input
future_benchmark
future_factor_return
performance_snapshot_mutation
position_history_mutation
pnl_reconciliation_break
attribution_reconciliation_break
hidden_residual
benchmark_lookahead
target_observation_confusion
posthoc_attribution
performance_claim_overstatement
```

Semantics:

- direct leakage → `FAIL`
- missing evidence → `NOT_TESTED`
- honest limitation → `NOT_TESTED`
- no automatic PASS

## 17. DETERMINISM

Identical:

```text
decision
+ OMS state
+ snapshot
+ benchmark
+ methodology
+ configuration
```

must produce identical:

- metrics
- attribution
- diagnostics
- hashes

## 18. CLI

Implement:

```text
quantlab monitor list
quantlab monitor inspect <id>
quantlab monitor run
quantlab monitor performance
quantlab monitor pnl
quantlab monitor returns
quantlab monitor attribution
quantlab monitor factor-attribution
quantlab monitor alpha-attribution
quantlab monitor exposure
quantlab monitor drift
quantlab monitor drawdown
quantlab monitor concentration
quantlab monitor turnover
quantlab monitor benchmark
quantlab monitor risk
quantlab monitor feedback
quantlab monitor reconcile
quantlab monitor report
```

Research aliases:

```text
quantlab research performance
quantlab research attribution
quantlab research portfolio-drift
quantlab research performance-feedback
```

## 19. DESKTOP

Add **Monitoring Lab** through `quantlab.app`.

Qt must only query application services.

UI may display:

- equity curve
- P&L decomposition
- attribution waterfall/table
- exposure
- drawdown
- drift
- benchmark comparison
- reconciliation
- feedback

Qt must not:

- parse Parquet
- query DuckDB directly
- calculate attribution
- modify historical observations
- modify decisions
- place orders

## 20. TEST REQUIREMENTS

Create comprehensive tests for:

- accounting identity
- realized/unrealized P&L
- return calculations
- security attribution
- factor attribution
- alpha lineage
- benchmark handling
- drift
- drawdown
- residual reconciliation
- PIT behavior
- immutability
- deterministic hashes
- knowledge ingestion
- ledger compatibility
- UI smoke

Minimum target: **50+ focused tests**, plus full regression.

## 21. SAFETY

```text
LIVE_TRADING = false
```

Prompt 19 must not import:

```text
kiteconnect
zerodha
openalgo
quantlab.brokers
```

No order creation or routing API.

## 22. NOT_TESTED POLICY

Do not fabricate:

- NIFTY history
- official holidays
- sector data
- market-cap data
- institutional benchmark data
- real broker TCA
- financing/borrow data
- tax data

## 23. DEFINITION OF DONE

Prompt 19 is complete only when:

- architecture inspected before implementation
- no existing engine duplicated
- tests pass
- ruff clean
- mypy strict for owned modules
- deterministic outputs verified
- attribution reconciles
- residuals are explicit
- PIT integrity is enforced
- Knowledge Graph lineage works
- ledger remains backward compatible
- desktop viewer works
- `LIVE_TRADING=false`
- documentation and ADR are complete
- synthetic data is clearly marked as diagnostic
- no result is promoted merely because performance is positive

## 24. FINAL ENGINEERING PRINCIPLE

A profitable portfolio observation is not automatically alpha.

The system must be able to conclude:

> **“The portfolio made money, but the evidence does not establish why.”**

That is a valid institutional research result.
