# Why this case exists

§9.10: "`order := by(c)` where `c` is **not a stored column, is computed**,
mixes types, or holds a non-finite spelling ... in any row (§6)." §6 says the
same: "`c` must be a stored column, never a computed one."

`flag` is computed by an `if`, which is the version most likely to slip through:
its values are small integers with a total order, its cells are empty like any
computed column's, and an implementation that checks "does this column have
comparable values in every row" rather than "is this column stored" finds
nothing wrong.

Nothing in §4.2 rule 10 relaxes §6, and the reason §6 gives is structural rather
than about the values: the sort key is `(typed value of c, key)`, and a computed
`c` would make the row order a function of the formula layer, which §7's
row-relative operators then read back — `cumulative` over an order derived from
a column the same evaluator is computing.
