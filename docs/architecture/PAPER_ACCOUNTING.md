# Paper accounting

**Status:** Prompt 18 / ADR-032  
**Version:** 1.8.0

A paper account is not `capital = portfolio market value`.

Books:

- cash
- reserved_cash
- available_cash = cash − reserved_cash
- positions (quantity, average cost, mark, realized/unrealized)
- gross/net exposure
- equity = cash + market_value
- fees / slippage / impact (attribution)
- turnover

Cash identity:

```
opening_cash + deposits − purchases + sales = closing_cash
```

Purchases and sales use simulated execution price × filled quantity. Explicit tax legs that are unspecified stay 0 with provenance `unspecified` / `NOT_TESTED`.

Shorting is off unless the paper account `allow_short` flag is true. Prompt 17 long-only policy is not silently overridden.

Broken identities raise `AccountingInvariantError` (FAIL).
