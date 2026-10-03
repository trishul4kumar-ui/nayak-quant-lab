# CI and branch protection

`main` should require the **CI / quality-and-test** workflow before merge. The
required checks are Ruff, strict mypy, the full test suite with a coverage
report, optimized-mode safety tests, and a distributable package build.

The coverage report is measured on every run but has no arbitrary global
threshold yet. Before adding one, establish stable coverage for the highest
risk packages: `execution_authorization`, `restricted_execution`,
`reconciliation`, `production_shadow`, `safety`, and `live_ops`.

The workflow deliberately does not run any live-market connection, load broker
credentials, or enable broker writes. Dependency-vulnerability and hosted
secret-scanning services should be enabled in the GitHub repository settings
when the repository owner chooses the provider and retention policy.
