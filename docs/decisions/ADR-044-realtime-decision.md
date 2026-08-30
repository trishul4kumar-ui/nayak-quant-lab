# ADR-044 — Real-Time Research-to-Decision Engine

## Context
Prompt 30 asked for a production-time decision cycle whose terminal output is `TargetPortfolio`, not an order. ADR-042 already names the broker gateway. This ADR is therefore **044**.

## Decision
Add `quantlab.realtime_decision`. Every production-like decision binds an explicit immutable `StrategyRelease`. Unknown, expired, or uncertified releases abstain or block. Never load an implicit “latest”.

```text
LIVE_TRADING = FALSE
DECISION ≠ ORDER
TARGET PORTFOLIO ≠ ORDER INTENT
```

Pipeline (composed, not forked):

```text
MarketState(T) → Features → Alpha → Regime → Adaptive → Model → Ensemble
→ Portfolio → Capital → Risk → InvestmentDecision → TargetPortfolio
```

AI may only `AI_SUGGESTION`. It cannot certify, promote, authorize, or create live orders.

Top-level CLI is `quantlab realtime-decision`. Desktop nav key is `rt_decision` (**Real-Time Decision Lab**).

## Consequences
- Prompt 17 capital types remain the target/decision records
- Comfortable with NO DECISION
- Same snapshot + release + config → same `decision_hash`
- This engine is not an OMS
