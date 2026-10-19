# Why this case exists

`order := by(n)` where the table has no column `n`, with two data rows.

§9.10 (`bad-order-column`): "`order := by(c)` where `c` is not a stored
column, is computed, mixes types, ..." There is no column `n`, so `n` is not
a stored column. §6: "`c` must be a stored column, never a computed one."

This is the twin of `parse/order-by-a-missing-column-with-no-rows-refused`,
and the two together pin that the row count does not decide the outcome.
`parse/order-unknown-col` already covers a missing order column with rows,
next to a `cumulative()` column and an aggregate over it. This case keeps the
table to the one fault, so it differs from its empty twin only in its rows.

`key := id` names a stored column with distinct values, so nothing else in
§9 applies.
