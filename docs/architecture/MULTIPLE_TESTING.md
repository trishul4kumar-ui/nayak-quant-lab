# Multiple testing

Every validation run records `research_family_id`, `n_hypotheses_in_family`, and `selection_stage` on the experiment row.

Available corrections (opt-in, method named in the report):

- Benjamini–Hochberg (FDR)
- Bonferroni (FWER)
- Holm

Deflated Sharpe (Bailey / López de Prado) is computed when `n_trials >= 2` and `n_periods >= 2`. Otherwise `NOT_TESTED`.

Probability of backtest overfitting: a simplified proxy requires at least eight paired IS/OOS trials. Full combinatorial CSCV is not manufactured.

A strategy found after a parameter grid is not equivalent to a pre-registered test.
