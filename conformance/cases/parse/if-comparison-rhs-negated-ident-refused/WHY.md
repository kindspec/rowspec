# Why this case exists

`order-rhs = signed / ident` and `signed = [ "-" *WSP ] literal`. The optional
minus belongs to `signed`, and `signed` wraps a **`literal`** — not an `ident`,
and not the `ident` alternative sitting beside it in `order-rhs`. So a bound may
be a negative number or a column, and never a negated column.

This is the case that keeps `signed` from being read as "a minus is allowed
here". A parser that implements `order-rhs` by calling `factor` — which is
`[ "-" *WSP ] primary` and looks like exactly the right shape — accepts `-b`,
and also accepts `-(a + 1)` and `-if(…)` while it is there. It would then be
speaking a larger language than the grammar generates, with no wrong number to
find later: `-b` evaluates perfectly well.

`parse/if-comparison-rhs-is-not-an-expression-refused` guards the same boundary
without a sign; this one guards it with the sign that `signed` just made legal
one token to the left. The pair is what pins `signed` to `literal`.
