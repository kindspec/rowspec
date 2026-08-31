# Why this case exists

§9.22 refuses an equality "whose left-hand `ident` ... names a **computed**
column ... — in a header cell and **on a declaration line alike**, since rule
5's reason is that a computed column has no cell text to compare, which is
true wherever the predicate is written."

`parse/predicate-lhs-names-a-computed-column-refused` pins the header-cell
half; this case pins the declaration half, which is easy to miss because a
declaration's `predicate` arrives through §4.1's `rhs`/`arg` rather than
through `group-call`, so an implementation with two predicate code paths can
check one and not the other. The wrong outcome is not a crash but a value:
the predicate matches nothing (a computed column's data cells are empty and
never equal `"p"`), and `sum` over an empty match set is `0` — the plausible
number rule 5 spends a paragraph on.
