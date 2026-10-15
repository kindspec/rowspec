# Why this case exists

A stored column is named `overflow`. In `r_1` it holds the text `x`, so
`c = overflow / z` is `#REF!(overflow)` there: the name of the column whose
value would not coerce (§8). In `r_2`, `c` divides by zero: `#REF!(/0)`.

§8: "**When its operands hold several different `#REF!` values, an aggregate
carries the one whose shape ranks first: `cycle`, then a name, then `/0`, then
`empty`, then `overflow`. Among several names it carries the one that sorts
first by code point over the NFC name, as §4.1.8 orders text.** Never the
first by row, in the file or in the declared order".

§8: "**The ranking reads a `#REF!` as it is spelled.** `#REF!(cycle)`,
`#REF!(empty)` and `#REF!(overflow)` rank as those shapes whatever produced
them, a broken reference to a column named `cycle`, `empty` or `overflow`
included."

Spelled `#REF!(overflow)`, the first error ranks as `overflow`, last, so
`s` is `#REF!(/0)`. A reader that ranked it as the name it originated as
would answer `#REF!(overflow)`.
`eval/aggregate-ranks-a-plain-name-over-div-zero` is the same table with
the column named `ov`.
