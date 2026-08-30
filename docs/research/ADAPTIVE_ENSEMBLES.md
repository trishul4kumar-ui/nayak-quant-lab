# Adaptive ensembles

Weights at T come from component ICs whose outcomes are available at T (label T−1→T). `max(mean IC, 0)` then hard constraints:

- `min_alpha_weight` / `max_alpha_weight`
- `max_concentration` (HHI)
- `min_active_alphas`

If constraints cannot be met, `InfeasibleAdaptiveEnsemble` is raised. They are not relaxed.

If every component mean IC is non-positive, equal weights are an **explicit** fallback, recorded in the note, not a silent recovery from future performance.

`ensemble_ic_mom` combines `rank_momentum_5` and `rank_momentum_20`. Direction stays `long_high`. Future component performance in the weight formula FAILs `future_ensemble_performance`.

`quantlab adaptive compare static_mom20 ensemble_ic_mom`  
`quantlab research adaptive-compare`
