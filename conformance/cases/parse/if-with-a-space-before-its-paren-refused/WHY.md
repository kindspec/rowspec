# Why this case exists

§4.2 rule 10: "rule 4 applies to its name unchanged: `if` is recognised only
immediately before `(`, so `| x = if |` is a reference to a column named `if`,
and `if (q > 0, 1, 0)` with a space is refused."

Rule 4 gives the mechanism: "The no-space rule is §4.1's: `rhs` is written
`ident "("` with no `*WSP` between them, and a header-cell call spells its
calls the same way." `cond = "if" "("` in §4.2's ABNF carries no `*WSP`
either.

Rule 8 explains why the whitespace rule is not uniform and cannot be relaxed
here: `WSP` is optional "between any two tokens of an `expr`", and the three
exceptions are all places where the token beside it is `ident`-shaped. This is
the third of them. Admitting the space would make `if` a reserved word by the
back door, since `| x = if (a) |` would then have to be a call rather than a
reference to a column named `if` followed by a parenthesised expression.

A hand-written parser that skips whitespace before dispatching on `(` — which is
what a generic tokeniser does — accepts this file.
