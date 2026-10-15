# Why this case exists

`a = g * 2` reads the per-row group aggregate `g = sum(v where k = @k)`,
which is 5, 2, 5 (§4.2 rule 5: `@k` is bound to the row being computed).
In the second row `g` is 2, so `a` is 4. No `order` is declared here; the
file order and the key order agree, so `row_index` 1 is `r_2` either way.

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

In file order the rows are `r_1` (`k` = `x`, `v` = 1), `r_2` (`y`, 2) and
`r_3` (`x`, 4). The `n` column is present but no `order` is declared.

Here the dependent column comes first in the header. The twin is
`rowrel/formula-over-a-later-sorting-group-aggregate-dependent-last`.
