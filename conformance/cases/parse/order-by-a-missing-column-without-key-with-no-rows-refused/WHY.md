# Why this case exists

`order := by(n)` with no `key` declared, no column `n`, and no data rows.
Two refusals apply, and neither depends on the rows.

- §9.25 (`order-without-key`): "`order := by(c)` in a table that declares no
  `key` (§6)." It is about the declarations alone.
- §9.10 (`bad-order-column`): "`order := by(c)` where `c` is not a stored
  column ..." It is about the header alone, and `n` is not in it.

§9: "the implementation reports the identifier of any one that applies, and
a case such as the `parse/two-refusals-*` ones names every identifier that
does." So `refusal` lists both, and reporting either passes. A reader that
checks the order only while sorting rows has nothing to sort here and would
accept, which fails.

`parse/order-by-a-missing-column-without-key-refused` is this table with two
rows.
