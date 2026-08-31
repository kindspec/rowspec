# Why this case exists

§7's second route to the empty aggregate: a table with no data rows at all.
Header and alignment row alone are a valid table (§9.21 refuses only a table
shorter than two lines), and every aggregate over it has an empty operand
multiset.

`sum` and `count` of nothing are `0`; `min`, `max` and `avg` of nothing are
`#REF!(empty)`. Here, unlike the all-blank sibling, `count` is `0` too — there
are no rows to count.
