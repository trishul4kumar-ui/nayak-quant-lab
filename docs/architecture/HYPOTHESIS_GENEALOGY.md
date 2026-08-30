# Hypothesis genealogy

A knowledge-level `HypothesisRecord` is distinct from `orchestration.hypothesis.HypothesisSpec` and `domain.research.ResearchHypothesis`.

Edges record `DERIVED_FROM`, `MUTATED_FROM`, `CROSSED_FROM`, `SIMPLIFIED_FROM`, and related operators. Prompt 15 candidate ancestry is retained when candidates are pruned: expression identity is the AST hash; per-candidate status lives on a `RESEARCH_RESULT` node so a later status cannot rewrite the expression.
