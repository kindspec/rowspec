# Why this case exists

Ordered by `n`, `p = prior(p)`, `q = delta(q)` and `r = cumulative(r)` each
name their own column, and `b = p + 1` reads `p`.

§4.2 rule 9: "A cycle evaluates to `#REF!(cycle)`, in every column on the cycle
and in every column whose formula depends, directly or transitively, on one."
§4.2 rule 10: "**Dependency and cycle analysis is over the whole formula, both
branches included, and is not affected by which branch a row selects.**"
SPEC.md makes no exception for the argument of a row-relative call, and rule 9
calls a cycle "a property of the whole header rather than of any one cell". So
each of `p`, `q` and `r` is on a cycle, and is `#REF!(cycle)` in every row,
the first row included, where `prior` and `delta` would otherwise be blank and
no earlier row is ever read: rule 10's `| x = if(c > 0, 0, x) |` "is
`#REF!(cycle)` in every row, including rows where `c` is positive and the cycle
is not reached".

This case asserts `b = p + 1`, which depends on the cycle: `#REF!(cycle)`.
