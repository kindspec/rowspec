# Why this case exists

`a = prior(g)` reads the per-row group aggregate `g = sum(v where k = @k)`.
§4.2 rule 5 binds `@k` to the row being computed, so `g` is 5, 2, 5 (group
`x` is 1 + 4, group `y` is 2). §7: `prior(c)` is "that column's value in
the preceding row", so `a` in the third row is `g` of the second row: 2.

§4.2 rule 9: "A formula may name any column, stored or computed, wherever that
column stands in the header. **The order of columns in the header is not an
input to any value**". "Evaluation is therefore by **dependency**: a formula's
operands are the values those columns themselves evaluate to. Where the
dependency graph is acyclic every column has exactly one value, and every
reader that respects dependencies computes it, whatever order it visits the
header in."

The dependent column's name sorts before the column it reads, so a reader that
visits computed columns in name order, or in header order when the dependent
comes first, reaches it before its input has a value. The table is acyclic.
This case and its twin hold the same columns with the two computed header
cells, and their cells, swapped; both expect the same value.

Ordered by `n`, the rows are `r_1` (`k` = `x`, `v` = 1), `r_2` (`y`, 2) and
`r_3` (`x`, 4). The declared order matches the file order.

Here the dependent column comes last in the header. The twin is
`rowrel/prior-over-a-later-sorting-group-aggregate-dependent-first`.
