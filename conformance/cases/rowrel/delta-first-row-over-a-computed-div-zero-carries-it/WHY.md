# Why this case exists

Ordered by `n`, the first row is `r_1`, where `c = a / z` is `1 / 0`,
`#REF!(/0)` (§4.2 rule 2).

§7: "In the first row, which has no preceding row, `delta(c)` is blank
only when `c` is a number, and otherwise carries the error `c` gives
there, a blank included, as it does in every later row."

§7: "Each operand carries the error it originated, so a computed `c`
holding `#REF!(/0)` here makes `delta(c)` `#REF!(/0)`, not a relabelled
`#REF!(c)`."

So `d` in the first row is `#REF!(/0)`, not blank and not `#REF!(c)`.

The row that comes first in the declared order is the second line of the
file. The other row's `c` is the number `1`, so a reader that takes "first"
from file position computes this row's `d` as `#REF!(/0) - 1`, which is
still `#REF!(/0)`; this case does not catch that reader. The number control,
`rowrel/delta-first-row-over-a-computed-number-is-blank`, does.
