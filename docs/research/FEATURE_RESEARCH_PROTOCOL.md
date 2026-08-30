# Feature research protocol

1. Write a hypothesis (direction, horizon, `pre_registered=false` unless actually pre-registered).
2. Pin a PIT snapshot (`dataset_id`, version, `snapshot_id`, checksum).
3. Take `Universe(T)` — never today’s survivors.
4. Compute the versioned feature from bars with `available_time <= T`.
5. Compute the forward label; reject if `label_end <= T`.
6. Align on the intersection of valid names; record `n`.
7. Quality, IC, quantiles, decay, correlation.
8. Integrity (including label-as-feature when panels are compared).
9. Prompt 05 gate if economic validation is requested. Feature IC alone does not promote.
10. Append the ledger. Do not delete a failed experiment.

Each lookback is a distinct experiment/version. Do not silently keep the best.

`quantlab feature list|inspect|compute|quality`  
`quantlab research feature <id> | ic | quantiles | decay | correlation`
