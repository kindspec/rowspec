# Why this case exists

The sibling of `rowrel/if-lazy-branch-guards-division-by-zero`, on the same
bytes, asserting the consequence one level up.

§8: "An aggregate over any column containing a `#REF!` is itself `#REF!` — **it
must not sum the values it can read**." So an eager implementation does not
merely get one cell wrong; `s` becomes `#REF!(/0)` and `n` — which §7 poisons on
a `#REF!` *actually present in the column* — becomes `#REF!(/0)` too. The
lazy answer is `5.0` (`20/4` plus the guard's `0`) and `2`.

`count` is asserted alongside `sum` for the reason
`eval/division-by-zero-is-ref-slash-zero` gives: §7's `count` carve-out is
scoped to values that merely fail to parse as numbers, not to an error value
sitting in the column.
