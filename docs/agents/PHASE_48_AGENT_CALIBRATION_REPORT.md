# Phase 48 — Agent Calibration and Performance Scoring

The local implementation stores immutable realized outcomes linked to memo, candidate,
level plan, optional position review, timestamped outcome, risk/cost/regime, and
paper/shadow status. No-trade rows require an explicit counterfactual flag.

The initial scoring model is intentionally inspectable: reliability bins, Brier score,
hit rate, coverage, and regime counts. It rejects future outcome labels relative to the
score date, refuses to label small samples as calibrated, and carries a hard
`self_modifying=False` boundary. Scorecards and outcomes are append-only and survive
restart.

The Agent Performance view shows raw versus calibrated fields, scorecard status,
sample size, reliability data, regime breakdown, and warnings. It does not feed a
score into adjudication automatically. Acceptance remains pending the consolidated
45–48 release gate.
