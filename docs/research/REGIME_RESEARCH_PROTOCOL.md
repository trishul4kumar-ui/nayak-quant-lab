# Regime research protocol

1. Write a hypothesis: the object is a **description of state**, not a forecast and not alpha.
2. Pin a PIT snapshot (`dataset_id`, version, `snapshot_id`, checksum).
3. Compute `StateSnapshot(T)` on `Universe(T)` (`available_time <= T`). Missing ≠ 0. Do not invent NIFTY.
4. Choose a versioned detector. Prefer the rule baseline before HMM or clustering.
5. Filtered / walk-forward paths only for anything that will be compared to a backtest. Smoothing and full-sample fits raise if `predictive=True`.
6. Keep hard labels and probabilities separate. Change-points are flags, not labels.
7. Report transitions (rows sum to 1) and run lengths. Do not treat them as remaining-duration forecasts.
8. Optional: conditional IC / covariance inside a contemporaneous regime. Thin samples are `NOT_TESTED`. Association is not causation.
9. Integrity: `future_regime` asserted on honest paths. `hmm_smoothing` / `full_sample_regime_fit` FAIL if used as predictive features. Prompt 05 gate. Synthetic cannot be `RESEARCH_CANDIDATE`.
10. Append the ledger (`regime_model_id`, identity hash, seed). Do not delete a failed experiment. Do not keep the best regime interaction silently.

Each detector / lookback / seed is a distinct experiment. Prompt 05 `regime_slices` (equity median-split of a backtest) is a different object.

`quantlab state list|inspect|compute`  
`quantlab regime list|inspect|fit|classify|transitions|durations|changes`  
`quantlab research regime <id> | regime-alpha | regime-risk | regime-correlation`
