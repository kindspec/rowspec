# Why this case exists

The argument of `sum` is `qty` with a trailing U+0001 START OF HEADING.

§4.1: `rhs = ident "(" *WSP arg *WSP ")"`, `arg = ident [ ... ]`, and `WSP`
is ASCII space and horizontal tab only. The character is a `Cc` control, not
`WSP` and not one of `ident`'s letters, marks, digits or `_`, so the line
does not match `declaration`. §4.1.11: "A declaration is malformed (§9.12)
if it contains `:=` and does not match `declaration` — including … any
`ident` violating rule 9." §3: "`Cf` format characters cannot appear in
identifiers".

§9.16 (`bad-identifier`) refuses an identifier containing "any character
outside `ident`". Following `parse/cf-in-key-declaration` and
`parse/cf-in-aggregate-name`, which put a `Cf` inside a declaration's
identifier, both identifiers are listed. The control is
`eval/declaration-argument-padded-with-space-and-tab`.
