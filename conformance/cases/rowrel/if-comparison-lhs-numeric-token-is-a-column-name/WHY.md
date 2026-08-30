# Why this case exists

§4.2 rule 7: "**Name positions** — the `ident` argument of `rowrel-call` and
`group-call`, §4.1's `arg`, either `ident` of an `equality`, the **left-hand
`ident` of a `comparison`** (rule 10), and the argument of `key` and `order` —
admit `ident` and have **no literal alternative**. `sum(123)` is the column named
`123`. So is `sum(1)`, and so is the `123` in `if(123 > 0, a, b)`."

That last clause is this case. `3` on the left of the operator is the column,
which holds `-5`, so `m` is `0`. Under the literal reading `3 > 0` is a constant
truth and `m` is `1` — in every row of every file, a formula that can never be
false and never says so.

The column's value is negative deliberately: with a positive value both readings
agree and the case would measure nothing.

Rule 7 also now gives the reason the two sides differ, which is the part an
implementer needs in order to stop looking for a mistake: "The two sides of a
comparison therefore read a bare `3` differently, which is the same asymmetry
`equality` already has in a `where` predicate — `ident` on the left, a value on
the right — and it is deliberate: the left of a comparison is the thing being
tested and the right is what it is tested against."

`eval/if-ordering-rhs-numeric-token-is-a-literal-not-a-column` is the other
side.
