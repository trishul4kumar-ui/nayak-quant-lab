# Model selection

Every tested configuration is a hypothesis.

Hyperparameters, feature subsets, PCA rank, and windows must be chosen on training/validation information only. Selecting on the holdout FAILs `holdout_contamination` and `future_hyperparameter`.

The experiment ledger records the family size (`n_hypotheses_in_family`). Do not treat the best of N trials as a single test.

Prompt 05 BH / Bonferroni / Holm remain the multiple-testing controls. PBO / CSCV stay `NOT_TESTED`.

Train-only selection: `quantlab model select select_ols_mom`
