# Why this case exists

Same bytes as `rowrel/prior-of-itself-is-cycle-in-the-first-row`. Ordered by
`n`, `p = prior(p)`, `q = delta(q)` and `r = cumulative(r)` each name their
own column, and `b = p + 1` reads `p`.

§4.2 rule 9: "A cycle evaluates to `#REF!(cycle)`, in every column on the cycle
and in every column whose formula depends, directly or transitively, on one."
§4.2 rule 10: "**Dependency and cycle analysis is over the whole formula, both
branches included, and is not affected by which branch a row selects.**"
SPEC.md makes no exception for the argument of a row-relative call, so each of
`p`, `q` and `r` is on a cycle and `#REF!(cycle)` in every row, the first row
included: rule 10's `| x = if(c > 0, 0, x) |` "is `#REF!(cycle)` in every row,
including rows where `c` is positive and the cycle is not reached".

This case asserts `r = cumulative(r)` in the first row, where a running
total has no previous total to read.
