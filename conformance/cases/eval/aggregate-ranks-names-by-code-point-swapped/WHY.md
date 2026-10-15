# Why this case exists

The computed `c` is `#REF!(a)` in `r_1` (it selects `a * 1` and `a` is the
text `x`) and `#REF!(Z)` in `r_2` (it selects `Z * 1` and `Z` is the text
`y`). §8: `#REF!(name)` carries "the column ... whose value would not
coerce". So `sum(c)` holds two names.

§8: "**When its operands hold several different `#REF!` values, an aggregate
carries the one whose shape ranks first: `cycle`, then a name, then `/0`, then
`empty`, then `overflow`. Among several names it carries the one that sorts
first by code point over the NFC name, as §4.1.8 orders text.** Never the
first by row, in the file or in the declared order".

`Z` is U+005A and `a` is U+0061, so by code point `Z` sorts first and
`s` is `#REF!(Z)`. A case-insensitive or locale order would pick `a`, as
would the header order, the formula order, or the first row of either
line order.

This case and its twin hold the same rows with the two data lines swapped. §6:
"Shuffling every line leaves all values unchanged." Both expect the same value.

The twin is `eval/aggregate-ranks-names-by-code-point`.
