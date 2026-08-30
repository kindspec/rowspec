# Why this case exists

§8: "**Under a `where`, 'any column' means the rows the predicate MATCHED.** A
`#REF!` sitting in a row the predicate excludes does not poison the aggregate."

This is the spec's own example made concrete: `r_03` is the only `B` row and
its `v` is `#REF!(/0)`. The three aggregates are the whole rule, on one table:

- `a_total` matches only clean rows, so it is a number, `8.0` — even though
  the *column* `v` contains an error.
- `b_total` matches the broken row, so it is `#REF!(/0)` — the operand set,
  not the predicate, is what carries the poison.
- `grand` has no `where`, so "any column" is every row and it is `#REF!(/0)`.

The pair is the point. An implementation that always scans the whole column
gets `a_total` wrong; one that treats a filtered aggregate as unpoisonable
gets `b_total` wrong. Either alone is satisfied by an implementation that
always does one thing; a case can only pin the boundary by standing on both
sides of it. The alternative §8 names — the literal whole-column reading —
makes one unrelated division by zero poison every group total in the table,
including groups whose every row is fine, which is exactly what `a_total`
being `8.0` forbids.
