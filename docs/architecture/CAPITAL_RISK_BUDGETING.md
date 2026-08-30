# Capital Risk Budgeting

**Status:** Prompt 17 / ADR-031  
**Version:** 1.7.0

Risk budgets are first-class inputs to capital allocation. They reuse Prompt 08:

- Portfolio variance `wᵀΣw` and volatility `√(wᵀΣw)`
- Marginal risk `(Σw)_i / σ_p` and contribution `w_i × MRC_i`
- Equal-risk / ERC via the existing optimizer
- Volatility targeting via `apply_vol_target`, bounded by leverage

Missing covariance is `NOT_TESTED`, never zero. If the target volatility requires leverage above the configured maximum, status is `TARGET_UNACHIEVABLE`. The engine does not silently lever up.

Kelly (`f* = μ/σ²`, binary `(bp−q)/b`) is a constrained research sizing method. Default `kelly_fraction = 0.25` with a cap. Unreliable inputs yield `KELLY_UNRELIABLE`.

VaR / expected shortfall are an interface. Samples below 60 observations remain `NOT_TESTED`.
