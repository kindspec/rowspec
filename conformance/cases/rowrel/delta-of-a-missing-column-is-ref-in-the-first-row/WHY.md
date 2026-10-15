# Why this case exists

`d = delta(nope)`, `p = prior(nope)` and `c = cumulative(nope)` name a column
that does not exist.

§8: "**A header error outranks every other error, and the leftmost rule
chooses among header errors.** A header error is one whose cause is in the
header alone: a name that does not resolve (§4.2 rule 10) ... A formula
holding one carries it in every row". §4.2 rule 10: "**A name that does not
resolve is `#REF!(name)` in EVERY row**", because "Whether `nope` resolves is
a property of the header alone: it is knowable before a single row is read,
it is the same for every row, and no edit to any cell can change it."

So each column is `#REF!(nope)` in every row, the first row included, where
`prior` and `delta` over a column that resolves would be blank. A blank there
would be the plausible non-answer §8 forbids: "A broken reference never
evaluates to zero, empty, or a stale value."

Ordered by `n`, the rows are `r_1` (`k` = `x`, `v` = 1), `r_2` (`y`, 2) and
`r_3` (`x`, 4). The declared order matches the file order.

This case asserts `d` in the first row.
