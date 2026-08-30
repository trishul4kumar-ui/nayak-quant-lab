# Hypothesis management

Hypotheses live in `quantlab.orchestration` as versioned `HypothesisSpec` objects.

Identity excludes timestamps. Changing the statement, null, universe, or horizon is a new version. The seed `H-MOM-001` is documentation, not engine-hardcoded alpha.

`domain.research.ResearchHypothesis` remains the Prompt 01 object used by the momentum slice. Orchestration does not replace it.

CLI: `quantlab hypothesis list|inspect|create|compare`.
