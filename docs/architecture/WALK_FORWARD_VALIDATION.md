# Walk-forward validation

Windows are generated from the session calendar of the PIT snapshot.

Kinds: `rolling`, `expanding`, `anchored` (anchored uses the same expanding start-at-origin rule).

Each window records:

- train start/end
- embargo gap
- purged training end (label-horizon overlap removed)
- test start/end

OOS P&L is the existing engine with `eval_start` / `eval_end`. History before the window remains in the bar set so lookback features are defined. The first included day turns over from a flat book.

The test set is not used to select lookback. Parameter surfaces are diagnostic.

See `quantlab.research.walkforward` and `quantlab.research.splits`.
