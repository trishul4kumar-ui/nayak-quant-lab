# Paper OMS architecture

**Status:** Prompt 18 / ADR-032  
**Version:** 1.8.0

Prompt 18 is the **paper order-management layer**. It turns an immutable `TargetPortfolio` into paper orders, simulated fills, paper positions, cash, and a reconciliation report. It does not place broker orders.

```
RESEARCH GATE → CAPITAL ALLOCATION → INVESTMENT DECISION → TARGET PORTFOLIO
                         HARD BOUNDARY
                              ▼
                         PAPER OMS
           intent → plan → paper order → paper fill
                    → position → cash → reconciliation
                              X
                         LIVE BROKER
```

Package: `quantlab.paper_oms`. Execution formulas remain Prompt 13. Capital decisions remain Prompt 17. The canonical P&L engine remains `quantlab.backtest.run_backtest`.

CLI: `quantlab paper …`. `quantlab capital` and `quantlab portfolio` are unchanged.

Accounting convention:

```
equity = cash + market_value
closing_cash = opening_cash + deposits - purchases + sales
rounded_qty = filled + remaining + cancelled + expired
```

BUY/SELL cash moves at the **simulated execution price** from Prompt 13 (friction is already in that price). TCA still reports spread, slippage, impact, and explicit cost as attribution, not a second debit.

Unknown liquidity is unfilled, not infinite. Official NSE holidays are `NOT_TESTED`.
