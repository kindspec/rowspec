# Why this case exists

Ordered by `n`, the first row is `r_1`, whose stored `v` is blank.

§7: "In the first row, which has no preceding row, `delta(c)` is blank
only when `c` is a number, and otherwise carries the error `c` gives
there, a blank included, as it does in every later row."

The error a blank `v` gives is `#REF!(v)`. §7: "If the row before this one
has a blank `c`, then `prior(c)` here is blank and `delta(c)` here is
`#REF!(c)`, because a difference needs a number", and "A blank `c` here
beside a stored cell beyond binary64 in the row before is `#REF!(c)`". §8:
"A blank cell is not zero."

So `d` in the first row is `#REF!(v)`, not blank.

The row that comes first in the declared order is the second line of the
file. The other row holds the number `5`, so a reader that takes "first"
from file position computes this row's `d` as the blank `v` minus `5`, which
is still `#REF!(v)`; this case does not catch that reader. The number
control, `rowrel/delta-first-row-over-a-computed-number-is-blank`, does.
