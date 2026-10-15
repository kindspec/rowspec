# Why this case exists

Column `a` holds the text `x` and 9×10^313 (a `9` and 313 zeros), whose
binary64 value is infinite. As operands of a coercing aggregate (§7), `x` is
`#REF!(a)` and the large cell is `#REF!(overflow)` (§8).

§8: "**When its operands hold several different `#REF!` values, an aggregate
carries the one whose shape ranks first: `cycle`, then a name, then `/0`, then
`empty`, then `overflow`. Among several names it carries the one that sorts
first by code point over the NFC name, as §4.1.8 orders text.** Never the
first by row, in the file or in the declared order".

§8: "A value that will not coerce counts as a name, so `sum(a)` over a
cell `x` and a stored cell beyond binary64 is `#REF!(a)` whichever line comes
first". All four coercing aggregates are asserted.

This case and its twin hold the same rows with the two data lines swapped. §6:
"Shuffling every line leaves all values unchanged." Both expect the same value.

The twin is `eval/aggregate-ranks-a-name-over-overflow`.
