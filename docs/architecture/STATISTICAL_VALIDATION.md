# Statistical validation

Default inference respects serial dependence.

- Moving-block bootstrap for a mean CI
- Sign-flip permutation for a two-sided p-value of mean return
- IID shuffle of returns is not offered
- Sample size < 8 periodic returns → `NOT_TESTED`
- Heteroskedasticity-robust regression inference is `NOT_TESTED` (no regression in this phase)
- Risk-free rate is the explicit zero convention in `Annualization`

A p-value is not a promotion criterion. Economic significance (costs, turnover, drawdown) is reported separately.
