# Why this case exists

The control for the two `parse/predicate-*-names-a-computed-column-refused`
cases. Rule 5 restricts the predicate's identifiers to stored columns; it does
not restrict the aggregated column, and it does not make group aggregates
harder to write. An implementation that closes the computed-column hole by
refusing predicates whose identifiers it has not resolved yet — during a pass
in which computed columns are not yet known — breaks this file, which is the
ordinary case §7 was written for.
