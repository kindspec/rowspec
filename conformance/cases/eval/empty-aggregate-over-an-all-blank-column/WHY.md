# Why this case exists

§7's third route to the empty aggregate, and the one §7 calls the reachable
one: rows exist, but the aggregate skips blanks, so the operand multiset is
empty anyway. This is what an ordinary optional column looks like before
anyone fills it in.

The identity-element contrast is asserted in the same table: `sum` of nothing
is `0.0` because that *is* the sum of nothing, while `min`, `max` and `avg`
have no identity element and are `#REF!(empty)`.

`n` is `2`, not `0`, and that is the subtle half of the pin. `count` counts
rows, and both rows exist — the blank-skip rule empties the multiset only for
the four type-committed aggregates. An implementation that reaches this route
by emptying "the column" rather than each aggregate's own operand multiset
reports `0` here and fails.

Siblings `empty-aggregate-where-matches-no-row` and
`empty-aggregate-over-a-table-with-no-data-rows` pin the other two routes;
§7 says the three are one condition with one answer, so the three cases
assert the same values for `s`, `lo`, `hi` and `m`.
