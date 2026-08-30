# Why this case exists, and the ambiguity it exposes

SPEC.md §4.1.9: "`ident` = 1*( LETTER / MARK / NUM / `_` / `-` / `.` )", where
"`LETTER`, `MARK` and `NUM` are the Unicode general categories `L*`, `M*`,
`N*`". ASCII digits are `Nd`, so `123` is a well-formed `ident` and a column may
be named `123`. The declaration grammar has no numeric-literal alternative --
`rhs = ident "(" *WSP arg *WSP ")" / ident` and `arg = ident` -- so `sum(123)`
can only mean the column named `123`.

By the letter of the grammar this file is valid, and that is what this case
asserts. `rowspec.table` accepts it; `rowspec_alt.table` refuses it with
"sum() takes a column".

**But I think §4.1 may not have meant it.** The section defines a grammar for
declarations and none at all for the header-cell *formula* language of §7 --
`total = qty * unit`, `net * 1.2`, `cumulative(c)`, `sum(x where y = @z)`. In
that undefined language a bare `123` is ambiguous between the column named `123`
and the numeric literal `123`, and §4.1.6 defines `number` precisely so that
literals have one spelling. Whichever way it is resolved, the resolution belongs
in §4.1 rather than in whichever reader gets there first. See
`design-findings/M0-adversarial-cases.md`.
