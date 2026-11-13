# Multiple testing

Every validation run records `research_family_id`, `n_hypotheses_in_family`, and `selection_stage` on the experiment row.

Available corrections (opt-in, method named in the report):

- Benjamini–Hochberg (FDR)
- Bonferroni (FWER)
- Holm

Deflated Sharpe (Bailey / López de Prado) is currently `NOT_TESTED`. Trial count and sample length alone do not identify it: calculation also requires the dispersion of trial Sharpe estimates, the independent/effective number of trials, verified selection, and identified moments of the selected return series. The previous standardized proxy is not a DSR and is no longer emitted. [Original methodology](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf).

Probability of backtest overfitting: a single pair of aggregate IS/OOS vectors cannot identify CSCV and yields `NOT_TESTED`. The suite can opt in to a descriptive CSCV calculation from aligned periodic trial returns; see the backtesting protocol for input requirements and limitations.

A strategy found after a parameter grid is not equivalent to a pre-registered test.
