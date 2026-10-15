# Why this case exists

The declaration `t := count()` has nothing between its parentheses.

§4.1's grammar for a declaration's right-hand side:

    rhs         = ident "(" *WSP arg *WSP ")" / ident
    arg         = ident [ 1*WSP "where" 1*WSP predicate ]
    ident       = 1*( LETTER / MARK / NUM / "_" )

§4.2: "a declaration's right-hand side matches `rhs` in its entirety or the
line is refused (§9.12). There is no partial parse and no fallback to text".

`ident` is `1*`, one or more characters, so an empty argument is not an
`arg` and the line does not match `declaration`. §9.12
(`malformed-declaration`) refuses "a line containing `:=` that does not
match `declaration`".

§9.16 (`bad-identifier`) lists the identifiers it covers as "column name,
aggregate name, `key`/`order` argument, or a value of the key column". An
aggregate function's argument is not in that list, and the list names the
`key`/`order` argument separately from "column name", so a reference to a
column is not read as a column name here. Only §9.12 applies, and the case
names it alone.

A reader that takes `t := count()` to mean "over no column" and answers `0`
produces a plausible number from a declaration the grammar does not
generate, which is the degradation §4 forbids: "A reader that cannot
recognise a construct MUST refuse it, and MUST NOT degrade a failed
recognition into a different successful one."

The control is `eval/declaration-arguments-that-are-idents-control`.

`count` is the aggregate most tempting to admit with no argument, because it
counts rows and never coerces (§7), so `count()` reads naturally as "how many
rows". The grammar gives it no such form: `count` takes an `ident` like the
other four.
