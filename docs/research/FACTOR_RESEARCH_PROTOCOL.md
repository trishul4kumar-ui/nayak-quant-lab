# Factor research protocol

1. Write a hypothesis: the characteristic is a **risk exposure**, not automatic alpha.
2. Pin a PIT snapshot (`dataset_id`, version, `snapshot_id`, checksum).
3. Take `Universe(T)` — never today’s survivors.
4. Compute the versioned factor (`available_time <= T`). Unsupported seeds stay `NOT_TESTED`.
5. Do not fill missing names with zero.
6. Quality, IC vs `forward_return(1)`, pairwise factor correlation.
7. Integrity: `future_factor` must be asserted on honest paths. A label used as a factor is FAIL.
8. Prompt 05 gate. Factor IC alone does not promote. Synthetic cannot be `RESEARCH_CANDIDATE`.
9. Append the ledger (`factor_id`, `factor_set`, identity hash). Do not delete a failed experiment.
10. Residualization creates a new factor identity.

Each lookback / neutralization is a distinct experiment. Do not silently keep the best.

`quantlab factor list|inspect|compute|exposure`  
`quantlab research factor <id> | factor-correlation`
