# Label engine

Labels are forward quantities. They are never feature inputs.

## Kinds

| Kind | Definition | Availability |
|---|---|---|
| `forward_return_H` | `P(T+H)/P(T)-1` | `T+H` |
| `forward_excess_return_H` | vs a PIT benchmark | `NOT_TESTED` without a benchmark series |
| `forward_volatility_H` | std of simple returns T→T+H | `T+H` |
| `forward_drawdown_H` | max drawdown of the close path | `T+H` |
| `forward_binary_direction_H` | 1 if forward return > 0 | `T+H` |

## Alignment

`feature.available_time <= decision_time` and `label_end > decision_time`. Ambiguous timestamps are rejected. This is compatible with Prompt 05 purge/embargo: the label for horizon H is not knowable until T+H.

Cash or an unavailable index is `NOT_TESTED`. NIFTY is not invented.
