# Online learning

Prequential evaluation is sequential:

1. Produce the prediction using only information available at T.
2. Freeze it.
3. When the outcome becomes available, score it.
4. Then update the learner.
5. Go to the next T.

This is **not** walk-forward refit, expanding IS/OOS windows, or a static model. Those remain Prompt 05 objects.

Insufficient history returns empty scores (`NOT_TESTED` that day), never a silent full-sample fit.

Learner updates use the PIT Spearman IC of the **underlying alpha** (outcomes available at T). Emitted predictions can be empty during warmup or a stale-gate; those empty scores are not used as the efficacy observation, or the gate could never accumulate history and never turn back on. Prequential IC still scores only what was emitted.

EWMA: `weight(age) = exp(-ln 2 / half_life)^age` with age in sessions and the newest observation age 0. Effective sample size is `(Σw)² / Σw²`. Short half-lives that drive ESS below `min_ess` are warned, not hidden.

Bayesian hit-rate uses a Beta(1,1) prior. The posterior mean is not certainty and not a live order. Credible intervals are a normal approximation when reported.

`quantlab adaptive prequential <id>`  
`quantlab research adaptive <id>`
