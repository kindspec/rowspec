# Why this case exists

The declaration `t := sum(n.x)` has an aggregate argument that is not an `ident`,
because it holds ``.``.

§4.1's grammar for a declaration's right-hand side:

    rhs         = ident "(" *WSP arg *WSP ")" / ident
    arg         = ident [ 1*WSP "where" 1*WSP predicate ]
    ident       = 1*( LETTER / MARK / NUM / "_" )

§4.2: "a declaration's right-hand side matches `rhs` in its entirety or the
line is refused (§9.12). There is no partial parse and no fallback to text".

§4.1.9: "**[CHOICE]** `-` and `.` are excluded, though an earlier draft
admitted them. The formula language uses `-` as subtraction, so a column named
`a-b` would be well-formed and permanently unreferenceable".

`n.x` is therefore not an `ident`, the line does not match
`declaration`, and §9.12 (`malformed-declaration`) refuses it: "a line
containing `:=` that does not match `declaration`", and §4.1.11 adds "any
`ident` violating rule 9".

The table has no column named `n.x`, though it has `n` and `x`. That keeps §9.16 out on the
header side. On the declaration side, §9.16 lists "column name, aggregate
name, `key`/`order` argument, or a value of the key column", and an
aggregate's argument is not among them, so only §9.12 applies and the case
names it alone.

The wrong outcomes this rules out are both quiet: reading `n.x` as one
column name, missing, gives `#REF!(n.x)`; reading it as arithmetic or
truncating at the punctuation gives a number. Neither is what §4.2 allows:
"There is no partial parse and no fallback to text".

The control is `eval/declaration-arguments-that-are-idents-control`.
