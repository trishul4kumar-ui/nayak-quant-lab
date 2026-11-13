# Corporate actions

See ADR-018.

The fabric stores corporate-action facts with an `available_time`. If the announcement time is unknown, it is stored as `None` and the event is treated as **unavailable**. QUANT LAB will not invent NSE circular timestamps.

Split adjustments are explicit (`PriceKind.ADJUSTED_PRICE`) and are applied only when both `available_time <= as_of` and `effective_date <= as_of`. An announced future split is not applied before it takes effect. For repeated `action_id` values, the latest revision available at the cutoff supersedes earlier revisions; conflicting same-time revisions fail closed. Input bars must have event and availability times no later than the cutoff. A relevant split with unknown availability, missing effective time, or invalid ratio raises an integrity error rather than being assumed absent.

Default research policy is **price return**. Dividends are not silently folded into close.

A dataset without a CA file is `corporate_actions = NOT_TESTED` on the research gate. That is not a PASS.

The action list and local split calculation do not establish completeness of a provider's history or certify historical availability. Price adjustment here is a price-only transformation; volume and dividend total return are not adjusted. Action revisions rely on stable action identifiers and supplied provenance; no real NSE corporate-action history is bundled.
