# Experiment design

A frozen `ResearchSpec` names the hypothesis, family, PIT snapshot, feature/alpha/portfolio/risk/execution identities, seed, budget, stopping rule, and primary metric.

Mutation after freeze is `experiment_identity_mutation` / `experiment_config_mutation`. Selection cannot migrate from the primary metric to whichever secondary looks strongest.

CLI: `quantlab experiment plan|run|report`.
