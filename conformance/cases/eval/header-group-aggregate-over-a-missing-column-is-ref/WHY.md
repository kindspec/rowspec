# Why this case exists

Same bytes as `parse/header-group-aggregate-over-a-missing-column-accepted`
and `rowrel/header-group-aggregate-over-a-missing-column-is-ref`. This one
asserts what a table-level aggregate over the broken column reports.

`t` is `#REF!(nope)` in every row (§8, §4.2 rule 7). `g := sum(t)` ranges
over a column holding that error, and §8 says "An aggregate over any column
containing a `#REF!` is itself `#REF!` — **it must not sum the values it can
read**", and "An aggregate poisoned by a `#REF!` among its operands carries
THAT error, unchanged." So `g` is `#REF!(nope)`: not `0`, and not a
relabelled `#REF!(t)`.
