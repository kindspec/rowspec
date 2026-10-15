# Why this case exists

The argument of `sum` is `qty` with a trailing U+200B ZERO WIDTH SPACE.

§4.1: `rhs = ident "(" *WSP arg *WSP ")"`, `arg = ident [ ... ]`, and `WSP`
is ASCII space and horizontal tab only. U+200B is a `Cf` format character, not
`WSP` and not one of `ident`'s letters, marks, digits or `_`, so the line
does not match `declaration`. §4.1.11: "A declaration is malformed (§9.12)
if it contains `:=` and does not match `declaration` — including … any
`ident` violating rule 9." §3: "`Cf` format characters cannot appear in
identifiers", because §4.1.9's allowlist excludes them.

§9.16 (`bad-identifier`) is not listed. Its list of identifiers is "column
name, aggregate name, `key`/`order` argument, or a value of the key column",
and an aggregate's argument is none of these: it is a reference to a column,
not the column's name in the header. §9.12 is the entry SPEC.md names for
this line. The control is
`eval/declaration-argument-padded-with-space-and-tab`.
