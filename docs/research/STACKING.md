# Stacking

```
BASE MODELS
  → walk-forward / OOS predictions
  → meta training matrix (labels available at T)
  → meta-model
  → composite score
```

The meta-model must not train on in-sample base predictions when those predictions are used as predictive evidence.

Incorrect:

```
fit base → predict the same training rows → train meta
```

Integrity: `stacking_leak = FAIL`.

Ridge and elastic-net stacking reuse Prompt 11 `fit_ridge` / `fit_elastic` / `predict_linear`.

`quantlab ensemble evaluate ridge_stack_mom`  
`quantlab research stacking`
