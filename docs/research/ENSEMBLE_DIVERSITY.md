# Ensemble diversity

Low correlation is not predictive value.

The engine reports pairwise Pearson / Spearman of contemporaneous component scores, mean absolute rank correlation, and `HIGH_REDUNDANCY` when mean |ρ| > 0.85.

Redundant components are not silently dropped. Pruning, if enabled, is an explicit threshold with a log of dropped IDs, and must use PIT history only.

Leave-one-out ΔIC measures marginal contribution. A strong component can still be redundant.

`quantlab ensemble diversity ew_mom_5_20`  
`quantlab research ensemble-diversity`
