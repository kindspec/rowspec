# Why this case exists

This is the boundary the `count` carve-out creates, asserted from the side that
keeps §8 intact.

SPEC §7: "`count` counts rows and never coerces. It is **poisoned by a `#REF!`
actually present in the column**, because that is an error value — but not by a
value that merely fails to parse as a number, because `count` never uses it as
an operand."

Here `doubled` is a computed column, and its second cell **evaluates to**
`#REF!(amt)`. That is an error value sitting in the column, not text that failed
to parse, so §8 applies unchanged: "An aggregate over any column containing a
`#REF!` is itself `#REF!`."

Without this case the carve-out has nothing holding its far edge, and the
natural next simplification — "`count` never poisons, it just counts rows" —
would pass the whole suite while silently reporting a row count for a column
full of errors. Compare `eval/ref-poisons-every-aggregate`, where the same bad
cell sits in a *stored* column and `count` correctly returns 3: same file shape,
same offending value, opposite answers, and the difference is exactly whether an
error value reached the column.
