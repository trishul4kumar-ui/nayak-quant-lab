# Ensemble selection

Searching combinations, windows, normalizations, and meta-models is a multiple-testing problem.

Every search records:

- candidate_count
- evaluated_count
- pruned_count / failed_count
- selection_rule

If `max_trials` truncates the search, `search_truncated` is reported. That is not exhaustive search.

Holdout observations must not choose the winner. `holdout_contamination = FAIL`.

Prompt 05 BH / Bonferroni / Holm remain the multiple-testing controls. PBO / CSCV stay `NOT_TESTED`.

Do not replace a champion solely because of higher historical Sharpe.

`quantlab ensemble select`
