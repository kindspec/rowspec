# Why this case exists

Same bytes as `parse/header-group-aggregate-over-a-missing-column-accepted`,
which explains why the file is accepted. This case asserts the cell's value.

§8: "A reference to a name that does not exist evaluates to `#REF!(name)`",
and §4.2 rule 7: "`sum(nope)` is `#REF!(nope)`". The group-call form adds a
predicate and changes nothing about the aggregated name: `t` is
`#REF!(nope)`.

The predicate `a = "x"` matches row `r_1`, so this is not the empty-match
route to `0`; and the predicate has no `@`, so every row's `t` is the same
value and `row_index` 0 is not choosing between rows. Whether a name
resolves "is a property of the header alone" (§4.2 rule 10), so no row may
read a number here.
