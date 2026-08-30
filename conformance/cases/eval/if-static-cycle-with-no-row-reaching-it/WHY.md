# Why this case exists

The sharpest form of §4.2 rule 10's static-analysis sentence: **no row in this
file reaches the cycle.** Every `c` is positive, so a data-dependent
implementation evaluates the `0` branch in all three rows, finds no recursion
anywhere, and reports `s = 0` and `n = 3`.

`0` is a plausible number, produced with no diagnostic, from a column the format
says is `#REF!(cycle)` in every row. That is the failure §1 exists to prevent,
and it is why this file has no row that would rescue a data-dependent reader.

`n` is asserted alongside `s` because §7 poisons `count` on a `#REF!` actually
present in the column, and `#REF!(cycle)` is one of §8's three shapes.
