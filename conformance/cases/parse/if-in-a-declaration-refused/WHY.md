# Why this case exists

§4.1's `rhs = ident "(" *WSP arg *WSP ")" / ident` and `arg = ident [ 1*WSP
"where" 1*WSP predicate ]`. A declaration's argument is a name, optionally
with a `where` clause, and nothing else — no comparison, no comma, no second
argument.

§4.2 states the general form of this directly: "A declaration is never an
`expr`: `g := sum(qty) * 2` is a malformed declaration (§9.12), not an
expression over an aggregate, because `rhs` has no arithmetic alternative and
none is added here." Rule 10 adds `cond` to `primary`, which lives in `expr`,
which a declaration never reaches.

The refusal is §9.12, a *line* containing `:=` that does not match
`declaration` — not §9.20, which §9.20's own text scopes away: "that entry is
scoped to a line containing `:=`, and a header cell is not one."

An implementation that shares one expression parser between header cells and
declaration right-hand sides — the obvious factoring, and the one that made
`if` cheap to add — accepts this line. It then has to decide what `a > 0` means
with no current row, which is the same hole §4.2 rule 5 documents for `@` on a
declaration line: "a table-level aggregate has no current row for `@` to refer
to. Any reading an implementation invents ... makes the predicate a filter the
author did not write."
