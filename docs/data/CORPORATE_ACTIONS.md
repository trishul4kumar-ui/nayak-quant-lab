# Corporate actions

See ADR-018.

The fabric stores corporate-action facts with an `available_time`. If the announcement time is unknown, it is stored as `None` and the event is treated as **unavailable**. QUANT LAB will not invent NSE circular timestamps.

Split adjustments are explicit (`PriceKind.ADJUSTED_PRICE`) and are applied only when `available_time <= as_of`.

Default research policy is **price return**. Dividends are not silently folded into close.

A dataset without a CA file is `corporate_actions = NOT_TESTED` on the research gate. That is not a PASS.
