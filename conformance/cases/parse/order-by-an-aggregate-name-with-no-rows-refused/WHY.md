# Why this case exists

`order := by(g)` where `g` is the name of a table-level aggregate,
`g := sum(a)`, and the table has no data rows.

§9.10 (`bad-order-column`): "`order := by(c)` where `c` is not a stored
column ..." An aggregate is not a column. §5: "A header cell is a NAME, or a
name and a formula separated by `=`", and the header here is `id` and `a`.
`g` is declared below the table and is one value for the whole table, not a
value per row, so it is no column at all, stored or computed. §6: "`c` must
be a stored column, never a computed one."

Column names and aggregate names are separate namespaces (§9.2, §9.3), so a
reader that resolves `by(g)` through any name it knows would find a value
here where it should find nothing. Whether the column is stored is decided by
the header, so the empty table changes nothing.
`parse/order-by-an-aggregate-name-with-rows-refused` is the same table with
two rows.

`key := id` names a stored column, and `g := sum(a)` is a well-formed
aggregate over a stored column, so nothing else in §9 applies.
