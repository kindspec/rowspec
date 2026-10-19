# Why this case exists

`order := by(g)` where `g` is the name of a table-level aggregate,
`g := sum(a)`, with two data rows.

§9.10 (`bad-order-column`): "`order := by(c)` where `c` is not a stored
column ..." `g` is declared below the table, not in the header, so it is not
a column (§5: "A header cell is a NAME, or a name and a formula separated by
`=`"). §6: "`c` must be a stored column, never a computed one."

With rows, `g` has a value (`3`), so a reader that resolved `by(g)` through
the aggregate names would have a number to sort by. It would give every row
the same order value, tie them all, and fall back to the key, and a
plausible order would come out. The twin
`parse/order-by-an-aggregate-name-with-no-rows-refused` pins the same
refusal with no rows.

`key := id` names a stored column with distinct values, so nothing else in
§9 applies.
