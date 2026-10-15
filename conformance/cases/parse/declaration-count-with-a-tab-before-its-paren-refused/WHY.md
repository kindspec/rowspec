# Why this case exists

The declaration is `g := count`, a tab, then `(qty)`.

§4.2 rule 4: the eight names of `rowrel-fn` and `agg-fn`, and `if`, "are
recognised **only** immediately before `(`, with no `WSP` between the
two." Rule 8 lists "**no** `WSP` between a function name and its `(`"
among the places where whitespace is not optional, and §4.1's `WSP`
is "ASCII space U+0020 and horizontal tab U+0009". §4.1: `rhs = ident "(" *WSP arg *WSP ")" / ident`, with no
`*WSP` between the `ident` and `(`, and §4.2 rule 4: "The no-space rule is
§4.1's: `rhs` is written `ident "("` with no `*WSP` between them".

The right-hand side matches neither alternative of `rhs`, and §4.2:
"a declaration's right-hand side matches `rhs` in its entirety or the line
is refused (§9.12)".
