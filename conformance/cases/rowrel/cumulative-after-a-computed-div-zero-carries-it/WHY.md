# Why this case exists

Ordered by `n`, the computed `q = a / z` is 1, `#REF!(/0)`, 1 (§4.2 rule 2:
"Division by zero evaluates to `#REF!(/0)`"). `c = cumulative(q)` adds each
value to the running total (§7), so the second step adds an error, and the
running total "propagates from there" (§7) as any error does (§8, "Errors
propagate; they never degrade").

§8: "`#REF!(name)` carries the *originating* name — the column that could not
be resolved or whose value would not coerce, not the column the error surfaces
in", and the same section's rule for an aggregate, "carries THAT error,
unchanged". `q`'s error is `#REF!(/0)`, so `c` carries `#REF!(/0)`, not a
relabelled `#REF!(q)`. `c` also sorts before `q` and is written before it.

This case asserts the third row, whose own `q` is 1: the running total
stays `#REF!(/0)` rather than restarting.
