# Why this case exists

`order := by(d)` where `d` is blank in every row. A key is declared, so
§9.25 does not apply, and nothing else in the file is refused.

§9.10 (`bad-order-column`) refuses an order column that "**is blank in any
row**". Every row is a case of "any row". §6 says the same: "**A blank cell
in `c` is refused** (§9.10)."

`parse/order-blank-cell-refused` and
`parse/order-blank-cell-in-a-text-column-refused` both have at least one
non-blank cell. This one has none, which is the input that separates
checking the blank rule from inferring the column's type: with no non-blank
cell there is no type to infer, nothing for "mixes types" to find, and an
implementation that only checks typed cells sees an empty set of types and
accepts. §9.10 names blank explicitly so that it does not depend on that
argument.
