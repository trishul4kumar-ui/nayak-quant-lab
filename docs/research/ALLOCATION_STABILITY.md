# Allocation Stability

Allocation stability measures how target weights and decision state move when inputs are perturbed (alpha, covariance, expected return, costs, risk target, constraints, capital).

Reported diagnostics:

- weight L1 stability
- rank stability (when ranks are defined)
- turnover sensitivity
- risk sensitivity
- decision-state sensitivity

A fragile allocation should be labeled as such. Perturbations used for diagnostics are not future information and must not rewrite the original decision hash.

Stress scenarios reuse Prompt 08 (`vol_shock`, `corr_shock`, return shocks). Stress is scenario analysis, not a forecast.
