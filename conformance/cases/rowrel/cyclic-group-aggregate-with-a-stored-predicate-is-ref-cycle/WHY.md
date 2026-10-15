# Why this case exists

Same bytes as
`parse/cyclic-group-aggregate-predicate-names-a-stored-column-accepted`.
`t` aggregates `u` and `u = t + 1` reads `t`. §4.2 rule 9: "A cycle
evaluates to `#REF!(cycle)`, in every column on the cycle". The
predicate `a = "x"` matches no row, so a reader that misses the cycle
through the aggregated column answers `0`, the empty sum. That no row
matches does not break the cycle: §4.2 rule 10 says "Dependency and cycle
analysis is over the whole formula ... and is not affected by which branch
a row selects", and rule 9 calls a cycle "a property of the whole
header".
