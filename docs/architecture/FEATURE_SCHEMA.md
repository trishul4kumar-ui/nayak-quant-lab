# Feature schema

A `FeatureDefinition` is not `domain.research.Feature` (a scalar at a timestamp) and not `data.fabric.features.FeatureSpec` (lookback/status for the store).

## Required fields

- `feature_id`, `version`, `name`
- `mathematical_definition`
- `inputs`, `lookback`, `frequency`
- `timestamp_semantics`: `available_time <= decision_time`; trailing windows only
- `universe_requirements`: `Universe(T)` at decision time
- `normalization`, `missing_value_policy`, `winsorization`
- `family` / `family_id`, `price_field`, `implementation_version`
- `operator`, `params`

`identity_hash` is `config_hash` of every field that changes meaning.

## Lifecycle

`DRAFT | TESTING | SUPPORTED | REJECTED | FRAGILE | REDUNDANT | CONTAMINATED | DEPRECATED`

There is no `PROFITABLE` status. Fabric `FeatureStatus` (`READY`, `INSUFFICIENT_HISTORY`, …) describes compute readiness, not research outcome.

## Missing values

Default policy is `NOT_AVAILABLE`. `missing ≠ 0`. `ZERO` is explicit. `FORWARD_FILL` uses only past values of the same name.
