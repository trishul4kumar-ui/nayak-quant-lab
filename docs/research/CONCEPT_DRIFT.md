# Concept drift

Drift is a change in the **realized IC process**. It is not a Prompt 09 market regime.

CUSUM on IC uses an expanding mean through t−1 (same spirit as `quantlab.regimes.change_points`). States: `STABLE`, `WATCH`, `DRIFT_DETECTED`, `INSUFFICIENT_DATA`, `UNAVAILABLE`.

Detecting drift does not automatically reset a model. `drift_triggered_refit` records a `ResetEvent` (old/new update counts, reason, threshold) and keeps only the last `min_obs` PIT ICs. The reset must not peek at future labels.

`quantlab adaptive drift <id>`
