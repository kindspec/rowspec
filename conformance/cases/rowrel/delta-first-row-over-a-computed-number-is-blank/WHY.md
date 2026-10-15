# Why this case exists

The control for `delta-first-row-over-a-computed-div-zero-carries-it`: the
same table with `z` of `2` in the first row, so `c` is the number `0.5`
there.

§7: "In the first row, which has no preceding row, `delta(c)` is blank
only when `c` is a number, and otherwise carries the error `c` gives
there, a blank included, as it does in every later row."

`c` is a number, so `d` in the first row is blank.

The row that comes first in the declared order is the second line of the
file, so a reader that takes "first" from file position answers for the
wrong row. §7: row-relative operators are "evaluated over the derived
order and never over file position".
