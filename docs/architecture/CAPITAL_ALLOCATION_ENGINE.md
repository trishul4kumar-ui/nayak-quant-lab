# Capital Allocation Engine

**Status:** Prompt 17 / ADR-031  
**Version:** 1.7.0

Prompt 17 is the **capital allocation / investment decision layer**. It turns validated research outputs into risk-aware, constraint-aware, capital-aware **target portfolios**. It does not place broker orders.

```text
CAPITAL ALLOCATION ≠ PORTFOLIO CONSTRUCTION ≠ ORDER ≠ EXECUTION ≠ BROKER
```

Package: `quantlab.capital`. Covariance, constructors, gate, ledger, and knowledge remain the Prompt 07 / 05 / 08 / 16 engines. Prompt 17 composes them.

Pipeline (no stage may use future information):

```text
research inputs → validation → PIT freeze → gate
  → expected return → risk / budget → capital budget → sizing
  → liquidity → constraints → optimization → vol target
  → turnover → drawdown state → abstention
  → TargetPortfolio → InvestmentDecision → ledger / knowledge
```

Outputs: immutable `InvestmentDecision` and `TargetPortfolio`. Not `Order`.

Desktop Capital Lab is a catalog of policies and the last decision. Qt does not compute allocations.

CLI: `quantlab capital …`. `quantlab portfolio` remains Prompt 07 construction.
