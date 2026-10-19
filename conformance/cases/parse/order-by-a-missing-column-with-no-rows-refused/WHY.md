# Why this case exists

`order := by(n)` where the table has no column `n` and no data rows.

§9.10 (`bad-order-column`): "`order := by(c)` where `c` is not a stored
column, is computed, mixes types, **is blank in any row**, or holds a
non-finite spelling ... in any row (§6)." The first clause is about the
header, not the rows: whether `c` is a stored column is decided by the
column names alone. §6 says the same: "`c` must be a stored column, never a
computed one." A table with no data rows still has a header, and `n` is not
in it, so the clause applies however many rows there are. The row-dependent
clauses (mixed types, blank, non-finite) have nothing to examine here, but
this case does not rest on them.

A reader that checks the order column only while sorting rows never looks at
a table with nothing to sort. That reader accepts a declaration that names
nothing, and the first row anyone adds turns the file into one it refuses.
`parse/order-by-a-missing-column-with-rows-refused` is the same table with
two rows.

`key := id` names a stored column, so §9.12's `key` clause and §9.25 do not
apply. Nothing else in §9 does.
