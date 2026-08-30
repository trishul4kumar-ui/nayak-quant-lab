# Model validation

Predictive validation is walk-forward (expanding by default). Prompt 05 already owns rolling / expanding / anchored / purge / embargo window construction; this engine does not replace it.

Adversarial paths that must FAIL:

- future scaler / PCA / selection / hyperparameter
- label used as a feature
- full-sample fit replayed as history
- holdout used for selection
- smoothed HMM regime as a predictive feature

Honest uncertainty: if a confidence interval is not justified, it is omitted. OLS is not causal. Complexity can overfit a zero-signal permutation.

Calibration (Brier, reliability) is `NOT_TESTED` until a probabilistic model is declared.

`quantlab model evaluate ols_mom`
