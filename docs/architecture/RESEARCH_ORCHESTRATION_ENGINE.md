# Research orchestration engine (control plane)

**Status:** Prompt 14 / ADR-028  
**Package:** `quantlab.orchestration`  
**Version:** 1.4.0

Orchestration is a **research control plane**. It does not replace PIT data, features, alphas, models, ensembles, portfolios, risk, execution research, the next-bar backtester, Prompt 05 validation, or the experiment ledger.

```
                    QUANT LAB
                        │
             RESEARCH CONTROL PLANE
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
   Hypothesis       Experiment       Research
    Registry          Registry         Family
        │               │                │
        └───────────────┼────────────────┘
                        ▼
                  Orchestrator
                        │
       ┌────────────────┼─────────────────┐
       ▼                ▼                 ▼
   Features           Models          Ensembles
       │                │                 │
       └────────────────┼─────────────────┘
                        ▼
                   Portfolio
                        ▼
                      Risk
                        ▼
              Execution Research
                        ▼
                  Backtester
                        ▼
                  Validation
                        ▼
              Multiple Testing
                        ▼
                  Falsification
                        ▼
                 Research Gate
                        ▼
              Existing Ledger
```

```
DATA ≠ FEATURE ≠ FACTOR ≠ ALPHA ≠ REGIME ≠ MODEL ≠ ADAPTIVE LEARNER
≠ ENSEMBLE ≠ PORTFOLIO ≠ ORDER INTENT ≠ EXECUTION
≠ RESEARCH EXPERIMENT ≠ RESEARCH HYPOTHESIS
```

A research experiment is an orchestration object. Discovery ≠ confirmation ≠ replication ≠ validation ≠ promotion.

Prompt 05 remains the only promotion gate. Synthetic families stay `WARN`. `LIVE_TRADING` remains false.

Desktop **Research Control** is a `quantlab.app` query viewer. It does not run grids or fit models.

The in-process orchestration registry stores defensive deep snapshots of research
families, search spaces, hypotheses, experiment specifications and plans, and
verifies their recorded hashes before returning copies. Legitimate hypothesis
status changes go through its validated transition method. A changed plan with
the same identity is rejected. These checks protect against accidental mutation
and detectable in-process alteration; they are not an authenticated or durable
preregistration archive, do not prove registration occurred before results were
seen, and do not establish independent holdout evidence. Durable, timestamped
family/selection records and complete trial accounting remain separate work.
