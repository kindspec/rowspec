# Why this case exists

`b = sum(p where k = @k)` is a per-row group aggregate over the computed
column `p = prior(v)`. §7: `prior(c)` is "that column's value in the preceding
row, blank included", so `p` is blank, 1, 2: the first row has no preceding
row (`rowrel/prior-first-row-blank`). §4.2 rule 5: "The aggregated column
itself carries no such restriction: `sum(total where region = @region)` over a
computed `total` is well-formed and rule 9 gives it a value." §7: "**A blank
cell is skipped by `sum`, `min`, `max` and `avg`**, and contributes nothing
rather than poisoning."

In the first row, `@k` is `x` (§4.2 rule 5 binds it to the row being
computed), the matched rows are `r_1` and `r_3`, their `p` values are blank
and 2, and `b` is 2.

§4.2 rule 9: "Where the dependency graph is acyclic every column has exactly
one value, and every reader that respects dependencies computes it, whatever
order it visits the header in." `b` depends on `p`, `p` on the stored `v`, and
nothing depends on `b`, so there is no cycle and `b` is not `#REF!(cycle)`. A
blank in a computed column is a value `prior` legitimately produces, not a
sign that the column has not been computed yet. `b` sorts before `p`.

Ordered by `n`, the rows are `r_1` (`k` = `x`, `v` = 1), `r_2` (`y`, 2) and
`r_3` (`x`, 4). The declared order matches the file order.

Here the aggregate comes last in the header. The twin is
`rowrel/group-aggregate-over-a-prior-column-aggregate-first`.
