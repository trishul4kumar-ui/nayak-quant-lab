# Symbolic research

Expressions are typed ASTs, not Python `eval`.

- Canonicalization: commutative `add`/`mul` sort children so `add(x,y)` ≡ `add(y,x)`.
- Conservative simplify: `x+0→x`, `x*1→x`, nested `rank(rank(x))→rank(x)`.
- Domain: `log`/`sqrt`/`div` drop undefined names; they do not coerce.
- Labels (`forward_*`, `future_*`) are forbidden primitives. A label in an expression is `label_as_feature` FAIL.

Human hypotheses may be entered as a tiny prefix form (`rank(momentum_20)`). That is not a general language.
