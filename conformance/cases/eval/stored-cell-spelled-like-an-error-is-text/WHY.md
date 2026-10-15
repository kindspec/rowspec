# Why this case exists

Column `a` holds `1` and a stored cell spelled `#REF!(zz)`. `#` inside a
table line is data (§4.1.10), and the cell does not match `number`, so by
§4.1.6 it is "text — `#REF!` when used as an arithmetic or aggregate
operand (§8)". It is not an error value: there is no column `zz`.

`sum` coerces (§7), so the cell is `#REF!(a)`, the column "whose value
would not coerce" (§8), and `s` is `#REF!(a)`, not `#REF!(zz)`.

§7: "`count` counts rows and never coerces"; it is poisoned only by a
`#REF!` "actually present in the column" as a value, and "not by a value
that merely fails to parse as a number". So `n` is `2`.
