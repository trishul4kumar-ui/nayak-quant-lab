# Risk research protocol

1. State that the object under test is a **variance/exposure model**, not expected return.
2. Pin the same PIT snapshot used for the portfolio or factor experiment.
3. Estimate `Σ(T)` with a named estimator (sample / EWMA / shrinkage) on PIT returns only.
4. Record PSD, min eigenvalue, condition number, and principal-risk shares.
5. Compute equal-weight-universe beta and implemented factor exposures. Missing ≠ 0.
6. Optional OLS: label the intercept as a model estimate, not validated alpha.
7. Run named stress scenarios. Do not treat PnL as a forecast.
8. Integrity: `future_covariance` / `future_factor` / `future_beta` asserted on honest paths.
9. Prompt 05 gate. Synthetic cannot promote. Multiple estimators are multiple hypotheses.
10. Append the ledger (`risk_model_id`, `risk_model_version`, `factor_set`).

Compare estimators only on identical dataset, universe, period, and costs.

`quantlab risk list|inspect|compute|exposure`  
`quantlab risk attribution|covariance|stress <experiment>`
