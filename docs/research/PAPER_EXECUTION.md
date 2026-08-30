# Paper execution

**Status:** Prompt 18 / ADR-032  
**Version:** 1.8.0

Paper execution reuses Prompt 13 scenario models:

`base`, `conservative`, `high_slippage`, `wide_spread`, `high_impact`, `low_liquidity`, `high_latency`, `partial_fill`, `stressed`.

`PaperExecutionAdapter` builds a Prompt 13 `OrderIntent` (the execution-research type) and calls `simulate_fill`. It does not invent spread, slippage, impact, or latency formulas.

A paper fill records reference price, arrival price, and simulated execution price separately. The note is always that the fill is simulated and not broker-confirmed.

Latency: no fill before arrival. Delayed-session quotes that are not in the PIT snapshot are not used; the seed path marks delayed-session price `NOT_TESTED` by continuing to use the as-of snapshot price.

Unknown volume → unfilled (or `NOT_TESTED` under policy). Never infinite ADV.
