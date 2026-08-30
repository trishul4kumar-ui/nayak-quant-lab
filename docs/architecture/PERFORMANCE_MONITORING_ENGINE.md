# Performance Monitoring Engine

**Version:** 2.1.0  
**ADR:** ADR-033

`quantlab.monitoring` consumes paper OMS positions and cash after a Prompt 17 decision. It is not a second backtester.

```
Equity_t = Cash_t + Σ(Position × Mark)
PnL_total = Realized + Unrealized + Income - Costs - Fees - Adjustments + Residual
```

Unknown legs remain `None`. Residual is visible. Profit is not automatically alpha.
