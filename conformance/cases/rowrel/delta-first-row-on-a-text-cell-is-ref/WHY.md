# Why this case exists

Ordered by `n`, the first row is `r_1`, whose stored `v` is the text `x`.

§7: "In the first row, which has no preceding row, `delta(c)` is blank
only when `c` is a number, and otherwise carries the error `c` gives
there, a blank included, as it does in every later row."

§8: "A value that will not coerce to a number is `#REF!`, not a guess", and
"`#REF!(name)` carries the *originating* name — the column that could not be
resolved or whose value would not coerce". The error `v` gives is
`#REF!(v)`, so `d` in the first row is `#REF!(v)`, not blank.

The row that comes first in the declared order is the second line of the
file. The other row holds the number `5`, so a reader that takes "first"
from file position computes this row's `d` as the text `v` minus `5`, which
is still `#REF!(v)`; this case does not catch that reader. The number
control, `rowrel/delta-first-row-over-a-computed-number-is-blank`, does.
