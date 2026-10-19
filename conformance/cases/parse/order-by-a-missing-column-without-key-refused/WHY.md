# Why this case exists

`order := by(n)` with no `key` declared and no column `n`, with two data
rows. Two refusals apply.

- §9.25 (`order-without-key`): "`order := by(c)` in a table that declares no
  `key` (§6)." §6: "`key` is **required** (§9.25)."
- §9.10 (`bad-order-column`): "`order := by(c)` where `c` is not a stored
  column ..." There is no column `n`.

§9 leaves the choice to the implementation: "When one file violates several
refusals, *which* is reported is deliberately unspecified: the implementation
reports the identifier of any one that applies, and a case such as the
`parse/two-refusals-*` ones names every identifier that does." So `refusal`
lists both, and reporting either passes. Accepting the file does not.

`parse/order-without-key` is the same §9.25 refusal with a valid order
column, and `parse/order-by-a-missing-column-with-rows-refused` is the §9.10
refusal with a key. `parse/order-by-a-missing-column-without-key-with-no-rows-refused`
is this table with no rows.
