# Agent scoring methodology

Only outcomes known at `as_of` are included. Each scorecard covers one immutable
agent id/version and a fixed outcome window. Raw confidence is never presented as
calibrated merely because it has a numeric value.

Scoring rejects outcomes recorded after the cutoff even if their realized period
ended earlier, policies created after the cutoff, and repeated outcome identities.
These checks use the recorded artifact timestamps; they do not independently prove
the timing, representativeness or independence of the underlying observations.

At fewer than the policy minimum of 20 scored outcomes, the status is `NOT_TESTED`,
calibrated confidence is null, and warnings remain visible. At sufficient sample size,
the current transparent baseline reports reliability bins, hit rate, and Brier score;
it is not an online learning model.

Any later use of calibration in adjudication requires a separately released policy,
offline and walk-forward validation, regression coverage, and explicit acceptance.
Recent performance cannot alter an agent's runtime permissions or behavior.
