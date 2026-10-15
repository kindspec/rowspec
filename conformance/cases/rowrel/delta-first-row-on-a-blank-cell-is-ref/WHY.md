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
file, so a reader that takes "first" from file position answers for the
wrong row. §7: row-relative operators are "evaluated over the derived
order and never over file position".
