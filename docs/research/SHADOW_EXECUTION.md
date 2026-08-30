# Shadow Execution

**Version:** 2.4.0

A shadow order is a hypothetical instruction derived from the same Δq as paper OMS. It is never routable. Fills reuse Prompt 13/18 models. Partial fills and residuals stay visible. Unknown volume is `NOT_TESTED`, not infinite liquidity.

Shadow fills must not use a later quote to improve an earlier simulated fill.
