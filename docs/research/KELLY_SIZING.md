# Kelly Sizing

Kelly is a **constrained research sizing method**, not a license to ignore risk.

```text
f* = μ / σ²
f* = (bp − q) / b     (binary payoff)
fractional = kelly_fraction × f*
capped = min(fractional, kelly_cap)
```

Default `kelly_fraction = 0.25`. Kelly must not override risk, drawdown, concentration, liquidity, factor, capital, or turnover limits.

If μ or σ² is missing or non-finite, status is `KELLY_UNRELIABLE`. The allocator abstains or uses only an **explicit** policy fallback — never a silent equal-weight switch.
