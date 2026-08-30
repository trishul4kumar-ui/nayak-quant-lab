# Risk model

**Status:** Prompt 08 (2026-08-30) — ADR-022  
**Package:** `quantlab.portfolio.covariance`, `risk_model`, `exposures`; research specs in `quantlab.risk.model`

The risk model must not secretly encode future returns. It is not an alpha model and not the live firewall.

## Covariance

Estimators on PIT-available simple returns (`available_time <= T`):

| Estimator | Notes |
|---|---|
| `sample` | `ddof=0` |
| `ewma` | λ default 0.94 |
| `shrinkage` | sample toward the diagonal, intensity default 0.2 |

`np.linalg.inv` is used in the optimizer path, not `pinv`. The matrix is symmetrized. Non-PSD fails unless `repair=eigenvalue_clip` is explicit. Condition number `> 1e12` fails.

`Σ(T)` does not change if later bars are appended. Cache keys include snapshot, names, as_of, lookback, estimator, repair, and shrinkage/λ.

## Diagnostics

`σ = sqrt(w′Σw)` at T. Marginal / component risk contribution. Volatility targeting scales `w` so forecast σ matches a cap, then `min(scale, max_leverage)`. This is not future realized vol.

## Beta and factors

Implemented: beta vs **equal-weight universe**. Documented as not an official index.

`NOT_TESTED` without PIT data: NIFTY/index beta, sector, size/value/quality, calibrated ADV/capacity, impact. Missing series stay `NOT_TESTED` / `NOT_AVAILABLE`. Missing beta is never assumed zero; a hard `max_beta` without a value raises `InfeasiblePortfolio`.

## Stress

Seed scenarios (`vol_up_50`, `corr_one`) are explicit. Results are labeled **not a forecast**.
