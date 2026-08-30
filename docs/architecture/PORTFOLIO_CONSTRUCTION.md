# Portfolio construction

**Status:** Prompt 07 (2026-08-30) — ADR-021  
**Package:** `quantlab.portfolio` (builder, baselines, spec, experiment)

Portfolio construction maps cross-sectional scores to **target weights**. Targets are not orders. The existing `construct_portfolio` + `RiskFirewall` + `run_backtest` path remains authoritative.

## Constructors

Transparent baselines (control experiments):

- top-N equal-weight long-only
- bottom-N equal-weight
- rank-weight (`w ∝ max(rank, 0)`)
- equal-weight names
- score-weight (`w ∝ max(score, 0)`)
- long-short top/bottom (gross 1, net ~0)

Optional optimizers (must beat a baseline out of sample to matter):

- min-variance (projected gradient on the simplex when long-only; not a commercial QP)
- mean-variance (`w ∝ Σ⁻¹ μ` where `μ` is the **alpha score**, not future return)
- long-only equal-risk contribution

There is no silent fallback optimizer. A failed solve is `OptimizationError` or `InfeasiblePortfolio`.

## Rebalance

`daily`, `weekly` (`session_index % 5 == 0`), `monthly` (month change). Off-rebalance dates hold the previous target; engine turnover is then 0.

## Experiments

`quantlab.portfolio.experiment` walks dates, builds a `WeightMapStrategy` (`Signal.score = target weight`), and calls the existing next-bar engine. `research/__init__.py` and `portfolio/__init__.py` stay thin.

Seed models: `mom20_topn`, `mom_5_20_ew`, `mom20_rank_weight`, `mom20_minvar`, `mom20_ls`.
