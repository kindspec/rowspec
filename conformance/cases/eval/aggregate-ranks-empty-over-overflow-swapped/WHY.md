# Why this case exists

The group aggregate `g = min(v where k = @k)` is `#REF!(empty)` in `r_1`:
its group `p` holds only a blank `v`, "A blank cell is skipped by `sum`,
`min`, `max` and `avg`", and "`min`, `max` and `avg` of nothing are
`#REF!(empty)`" (§7). It is `#REF!(overflow)` in `r_2`, whose group holds
9×10^313 (§8). `s := sum(g)` holds both.

§8: "**When its operands hold several different `#REF!` values, an aggregate
carries the one whose shape ranks first: `cycle`, then a name, then `/0`, then
`empty`, then `overflow`. Among several names it carries the one that sorts
first by code point over the NFC name, as §4.1.8 orders text.** Never the
first by row, in the file or in the declared order".

`empty` ranks before `overflow`, so `s` is `#REF!(empty)`.

This case and its twin hold the same rows with the two data lines swapped. §6:
"Shuffling every line leaves all values unchanged." Both expect the same value.

The twin is `eval/aggregate-ranks-empty-over-overflow`.
