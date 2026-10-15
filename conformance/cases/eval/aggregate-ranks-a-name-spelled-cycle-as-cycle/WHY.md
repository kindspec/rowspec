# Why this case exists

A stored column is named `cycle`; the table has no cycle. `c` is `#REF!(b)`
in `r_1` (the text `x` in `b`) and `#REF!(cycle)` in `r_2` (the text `y` in
the column `cycle`).

§8: "**When its operands hold several different `#REF!` values, an aggregate
carries the one whose shape ranks first: `cycle`, then a name, then `/0`, then
`empty`, then `overflow`. Among several names it carries the one that sorts
first by code point over the NFC name, as §4.1.8 orders text.** Never the
first by row, in the file or in the declared order".

§8: "**The ranking reads a `#REF!` as it is spelled.** `#REF!(cycle)`,
`#REF!(empty)` and `#REF!(overflow)` rank as those shapes whatever produced
them, a broken reference to a column named `cycle`, `empty` or `overflow`
included."

Spelled `#REF!(cycle)`, the second ranks as `cycle`, first, so `s` is
`#REF!(cycle)`. Read as two names, `b` would sort first by code point and
the answer would be `#REF!(b)`.
