# Model research

A statistical model is a research object. It is not alpha and not an order.

Required baseline hierarchy:

```
NO-SIGNAL → MEAN → EXISTING ALPHA → OLS → REGULARIZED → NONLINEAR
```

The question is incremental information, not standalone R² or accuracy.

Walk-forward evaluation:

1. Fit using only labels whose `available_time` is ≤ T.
2. Freeze the state (`available_information_cutoff`).
3. Predict with features available at T.
4. Score when the T→T+1 label arrives.

Synthetic IC is not market evidence. Prompt 05 remains the only promotion gate.

`quantlab model evaluate ols_mom`  
`quantlab research model ols_mom`  
`quantlab research model-compare`
