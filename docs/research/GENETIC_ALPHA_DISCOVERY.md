# Genetic alpha discovery

Genetic search in QUANT LAB is a **bounded, seeded, recorded** search over typed expression trees.

- Population, generations, and max candidates are frozen before the run.
- Every candidate is archived, including invalid and redundant trees.
- Fitness uses train-fold IC plus complexity/redundancy/turnover penalties. Sharpe is not the objective.
- Holdout is scored after selection and is not an input to tournament or stopping.
- Extending the budget after seeing results is `posthoc_search_budget` FAIL.

Seed family: `GP-MOM-VOL-001` (momentum and realized-vol features already in the Prompt 06 library). Synthetic output is architecture evidence, not market evidence.
