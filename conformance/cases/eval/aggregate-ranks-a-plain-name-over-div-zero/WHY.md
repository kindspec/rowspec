# Why this case exists

The control for `eval/aggregate-ranks-a-name-spelled-overflow-as-overflow`:
the stored column is named `ov`, so `c` is `#REF!(ov)` in `r_1` and
`#REF!(/0)` in `r_2`.

§8: "**When its operands hold several different `#REF!` values, an aggregate
carries the one whose shape ranks first: `cycle`, then a name, then `/0`, then
`empty`, then `overflow`. Among several names it carries the one that sorts
first by code point over the NFC name, as §4.1.8 orders text.** Never the
first by row, in the file or in the declared order".

A name ranks before `/0`, so `s` is `#REF!(ov)`.
