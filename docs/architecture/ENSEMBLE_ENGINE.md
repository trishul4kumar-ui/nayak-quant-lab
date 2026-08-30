# Ensemble / meta-alpha engine

**Status:** Prompt 12 (2026-08-30) — ADR-026  
**Package:** `quantlab.ensemble`  
**CLI:** `quantlab ensemble`

Distinct from Prompt 07 `quantlab.alpha.ensemble` (portfolio signal combinations) and from `quantlab research ensemble` (that command still inspects Prompt 07 alpha ensembles).

An ensemble emits a research-time score. It is not a portfolio, not alpha, and not an order.

```
COMPONENTS AT T → FREEZE → COMBINE AT T → FREEZE ENSEMBLE → PREDICT → REALIZE T→T+1
```

```
ENSEMBLE ≠ PORTFOLIO
META-ALPHA ≠ ALPHA ≠ ORDER
```

## Weighting

Equal-weight (`w_i = 1/N`) and best individual component are mandatory baselines.

| ID | Policy |
|---|---|
| `ew_mom_5_20` | equal |
| `static_ic_mom` | expanding PIT IC |
| `invvol_mom` | inverse IC vol |
| `corr_mom` | Prompt 08 diagonal shrinkage on component-IC covariance |
| `roll_ic_mom` | rolling IC; `max(IC, 0)`; no sign flip |
| `ewma_ic_mom_ens` | Prompt 10 EWMA IC |
| `ridge_stack_mom` / `elastic_stack_mom` | walk-forward OOS stacking |
| `meta_ols_mom` / `rank_meta_mom` | meta-alpha |
| `hetero_alpha_ols` | ALPHA + MODEL |
| `regime_ew_mom` | equal + PIT `vol_tercile` |

Component-IC covariance reuses the Prompt 08 shrinkage formula. It is not a second asset-covariance engine.

## Stacking

Meta-models train only on walk-forward out-of-sample base scores whose labels are available at T. Fit-base-then-train-meta on the same in-sample rows is `stacking_leak = FAIL`.

## Gate

Prompt 05 remains the only promotion authority. Synthetic results cannot become `RESEARCH_CANDIDATE`.

`quantlab ensemble evaluate ew_mom_5_20`  
`quantlab research meta-alpha`  
`quantlab research ensemble-compare`
