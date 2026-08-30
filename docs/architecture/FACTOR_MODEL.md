# Factor model

**Status:** Prompt 08 (2026-08-30) — ADR-022

When exposures `B` and a factor covariance `Ω` exist:

```text
Σ ≈ B Ω B′ + D
```

`D` is the diagonal of leftover asset variance after the systematic piece. Negative idiosyncratic variance fails rather than being hidden. Missing `B` or `Ω` leaves factor-vs-idiosyncratic split `NOT_TESTED`; asset-level `w′Σw` from Prompt 07 still applies.

OLS of returns on factors labels the intercept **model intercept estimate**. It is not validated alpha.

Official-index (NIFTY) beta stays `NOT_TESTED`. Equal-weight-universe beta is the implemented market proxy and must not be relabeled as an index beta.
