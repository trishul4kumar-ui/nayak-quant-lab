# Statistical model engine

**Status:** Prompt 11 (2026-08-30) — ADR-025  
**Package:** `quantlab.learning`  
**CLI:** `quantlab model`

`quantlab.models` remains the experiment ledger. This package is the statistical-learning engine.

A model may emit a research-time score. It may not create a broker order.

```
TRAIN (labels available at T)
→ FREEZE
→ PREDICT at T
→ REALIZE label T→T+1 when available
```

Fitting on the full sample and replaying “historical predictions” is leakage unless marked leaky.

## Seed models

| ID | Algorithm |
|---|---|
| `no_signal` | constant zero |
| `mean_baseline` | training mean |
| `alpha_mom20` | Prompt 06 `rank_momentum_20` passthrough |
| `ols_mom` | pooled OLS |
| `ridge_mom` | ridge |
| `lasso_mom` | lasso |
| `elastic_mom` | elastic net |
| `huber_mom` | Huber IRLS |
| `rf_mom` | shallow random forest |
| `gb_mom` | shallow gradient boosting |
| `pca_ols_mom` | train-only PCA then OLS |
| `select_ols_mom` | train-only univariate IC then OLS |
| `regime_ols_mom` | OLS with PIT `vol_tercile` |

Missing values are dropped. They are never filled with zero. Scaling, selection, and PCA are training-window only.

`learning/__init__.py` does not import `experiment`.

`quantlab model list|inspect|fit|predict|evaluate|stability|importance|residuals|compare|select`
