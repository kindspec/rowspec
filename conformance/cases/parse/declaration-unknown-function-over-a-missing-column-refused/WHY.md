# Why this case exists

The declaration `g := median(nope)` calls a function that is not one of the
five aggregates, over a column that does not exist.

§7: "Functions: `sum`, `count`, `min`, `max`, `avg`. An unknown function is
refused." §9.11 (`unknown-aggregate`): "an unknown aggregate function". The
missing column would be a value, `#REF!(nope)` (§8, §4.2 rule 7), but only in
a file that is accepted, and §9 says an implementation "MUST refuse" this one.

Only one identifier applies. The line matches §4.1's `declaration`
(`ident := ident "(" arg ")"`, and `rhs` does not restrict the function name),
so §9.12 (`malformed-declaration`, "a line containing `:=` that does not match
`declaration`") does not apply. §9.20 (`malformed-formula`) is scoped to a
header cell and says "§9.12 does not reach it: that entry is scoped to a line
containing `:=`, and a header cell is not one"; a declaration is not a header
cell, so §9.20 does not reach this line either. (The same call in a header
cell would meet both §9.11 and §9.20, as
`parse/uppercase-if-is-an-unknown-function-refused` does.)

The failure this pins is a reader that resolves the argument before the
function and reports `#REF!(nope)`.
