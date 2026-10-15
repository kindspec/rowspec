# Why this case exists

`c = sum(c where k = @k)` aggregates its own column, and `b = c * 2` reads it.
§4.2 rule 9: "A cycle evaluates to `#REF!(cycle)`, in every column on the cycle
and in every column whose formula depends, directly or transitively, on one",
and evaluation is by dependency: "a formula's operands are the values those
columns themselves evaluate to". §4.2 rule 5: the aggregated column "carries no
such restriction" as the predicate's names, so the file is accepted and the
answer is a value. `c`'s data cells are empty (§5), so a reader that reads them
instead of detecting the cycle answers `0`, the empty sum.

No `order` is declared; file order and key order agree.

This case asserts `c` in the first row.
