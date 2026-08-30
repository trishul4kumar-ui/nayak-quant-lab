# Model stability

A high OOS IC with flipping signs is a warning, not a promotion.

Diagnostics:

- coefficient sign changes across expanding refits
- permutation IC drop (frozen model, OOS features shuffled)
- residual mean / variance / lag-1 autocorrelation
- IC half-life via Prompt 10 `estimate_half_life`

Feature importance is not causal importance. Correlated momentum features make importance unstable.

`quantlab model stability ols_mom`  
`quantlab model importance ols_mom`  
`quantlab research model-stability ols_mom`
