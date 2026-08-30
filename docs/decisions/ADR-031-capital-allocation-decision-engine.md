# ADR-031 — Capital allocation and investment decision engine

## Context
Prompt 17 asks QUANT LAB to answer: how much capital, to which validated opportunities, under which risk/constraint budget, with what target portfolio at T, why, and whether the decision is reproducible from the frozen PIT snapshot — without placing broker orders.

Prompts 01–16 already own the PIT fabric, backtester, covariance, research gate, risk firewall, JSONL ledger, execution-research layer, orchestration, discovery, and knowledge graph. A second copy of any of those would fork scientific identity.

## Problem
Without an explicit capital-allocation layer, portfolio construction is mistaken for an investment decision, targets look like orders, capital is silently equated with portfolio value, hard limits get clipped, and synthetic research is treated as production allocation.

## Options
1. Extend Prompt 07 constructors until they emit orders
2. Add `quantlab.capital` as a decision engine that consumes existing portfolio, risk, gate, and knowledge outputs and emits immutable `TargetPortfolio` / `InvestmentDecision` objects
3. Wait for Prompt 18 Paper OMS and fold allocation into order planning

## Decision
Option 2.

1. Capital allocation is separate from portfolio construction. Prompt 07 still produces cross-sectional weights; Prompt 17 sizes, budgets, constrains, and records the capital decision.
2. Target portfolios are separate from orders. Prompt 17 must not construct `Order` or `OrderIntent`.
3. Broker integration is prohibited. `LIVE_TRADING` remains false; production allocation refuses to initialize if live trading is true.
4. Capital accounting is explicit (equity, cash, reserved, investable). Capital is never silently set equal to portfolio value.
5. Risk budgets are first-class and reuse Prompt 08 covariance / ERC / vol targeting. Missing covariance is `NOT_TESTED`, not zero.
6. Kelly is a constrained research sizing method (default fraction 0.25, capped). It cannot override hard limits. Unreliable inputs yield `KELLY_UNRELIABLE`.
7. Abstention is a valid decision (`REJECTED` / `ABSTAIN` / `RESEARCH_ONLY`). Failed and infeasible candidates are retained.
8. Hard constraints cannot be silently relaxed, clipped, or fallback-sized unless the policy names an explicit fallback.
9. PIT is mandatory. A decision at T may use only information with `available_time <= T`. Future rows appended after T must not change the hash.
10. Decisions are immutable. A material change creates a new decision.
11. Decision hashes are required and canonical (snapshot, policy, inputs, software version).
12. Synthetic data cannot promote through Prompt 17 (`RESEARCH_ONLY` at best).
13. Prompt 05 remains the only research gate. FAIL prohibits allocation. Prompt 17 does not introduce `LIVE_READY`.
14. Prompt 18 owns order lifecycle. Prompt 17 stops at `TargetPortfolio`.

## Consequences
- `CAPITAL ALLOCATION ≠ PORTFOLIO CONSTRUCTION ≠ ORDER ≠ EXECUTION ≠ BROKER`
- Integrity gains capital leak flags; unimplemented remain `NOT_TESTED`. `future_covariance` is reused, not duplicated.
- Desktop Capital Lab is a query viewer of `quantlab.app.capital`.
- `quantlab portfolio` remains Prompt 07. Capital CLI is `quantlab capital …`.

## References
Prompt 17; ADR-021, ADR-022, ADR-027, ADR-028, ADR-030
