# Why this case exists

`key := nope` in a table that has no column named `nope`.

§4.1.11: "**`key := col` is malformed too when `col` is not a stored column
of the table** — when no column has that name, or the column it names is
computed." §9.12 (`malformed-declaration`) lists the same thing: "a
`key := col` whose `col` is not a stored column of the table: no column of
that name, or a computed one". §6 repeats it: "`key :=` naming no column, or a
computed one, is refused (§9.12)."

The line matches `declaration` syntactically (`ident`, `:=`, a bare `ident`),
so the refusal is the semantic one §4.1.11 adds, not a grammar failure.

Nothing else in the file is refused, so `malformed-declaration` is the only
identifier §9 allows. The column names, the row ids and the formula
`b = a * 2` are all well-formed, the computed cells are empty (§9.17), and no
`order` is declared, so §9.10 and §9.25 cannot apply. With no column named
`nope` there is no key column whose values §9.5 or §9.16 could inspect.

`parse/key-names-a-stored-column-accepted` is the same table with
`key := id`, which is accepted.
