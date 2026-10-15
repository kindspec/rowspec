# Why this case exists

The computed `c = a / z` is `#REF!(overflow)` in `r_1` (its operand `a` is
9×10^313, infinite as binary64, §8) and `#REF!(/0)` in `r_2` (§4.2 rule 2).

§8: "**When its operands hold several different `#REF!` values, an aggregate
carries the one whose shape ranks first: `cycle`, then a name, then `/0`, then
`empty`, then `overflow`. Among several names it carries the one that sorts
first by code point over the NFC name, as §4.1.8 orders text.** Never the
first by row, in the file or in the declared order".

§8: "`sum(c)` over a computed `#REF!(overflow)` and `#REF!(/0)` is
`#REF!(/0)`." `count` is asserted too: "`count` coerces nothing, so only the
`#REF!` values actually present compete in it", and both errors are values
actually present in `c`, so `count(c)` is `#REF!(/0)` as well.

This case and its twin hold the same rows with the two data lines swapped. §6:
"Shuffling every line leaves all values unchanged." Both expect the same value.

The twin is `eval/aggregate-ranks-div-zero-over-overflow`.
