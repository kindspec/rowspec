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
file, so a reader that takes "first" from file position answers for the
wrong row. §7: row-relative operators are "evaluated over the derived
order and never over file position".
