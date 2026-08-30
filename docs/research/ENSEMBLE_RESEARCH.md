# Ensemble research

An ensemble is a research object. The question is incremental information, not a prettier combination.

Required comparison:

```
best individual component
vs equal-weight (w_i = 1/N)
vs candidate
```

where the candidate may be static, correlation-aware, dynamic, meta-alpha, or stacked.

Walk-forward:

1. Components available at T are frozen.
2. Weights / meta-models use only evidence whose `available_time` is ≤ T.
3. The ensemble is frozen.
4. Predict at T.
5. Score when the T→T+1 label arrives.

Synthetic IC is not market evidence. Prompt 05 remains the only promotion gate.

`quantlab ensemble evaluate ew_mom_5_20`  
`quantlab ensemble compare ew_mom_5_20 ridge_stack_mom`  
`quantlab research ensemble-compare`
