# Why this case exists

All four of `order-op` on the boundary value, in one header, so that no
implementation passes by getting two of them right.

`order-op = "<=" / ">=" / "<" / ">"`, and the alternation matters at the lexer:
a reader that tries `<` before `<=` consumes the `<` of `<=` and then finds `=`
where an `order-rhs` should be. Such a reader refuses `q <= 0` — or, worse,
reads `q < = 0` as `q < 0` with stray text and, if it is lenient about trailing
tokens, answers `0` where the format answers `1`.

The value `0` is chosen because it is the only value at which strict and
non-strict disagree, and because it is the value every guard in the corpus is
written about.
