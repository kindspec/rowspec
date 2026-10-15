# Why this case exists

`key := b` where `b` is the computed column `b = a * 2`.

§4.1.11: "**`key := col` is malformed too when `col` is not a stored column
of the table** — when no column has that name, or the column it names is
computed. ... a computed column's cells are empty (§5), so neither holds a row
id." §9.12 (`malformed-declaration`) names "a `key := col` whose `col` is not
a stored column of the table: no column of that name, or a computed one".

The table has no data rows, deliberately. A computed column's data cells must
be empty (§5, §9.17), so with any data row the key column would hold blank
values, and a reader could argue that §9.16 (`bad-identifier`: "a value of the
key column" that is not an `ident`) or, with two rows, §9.5
(`duplicate-row-id`) applies as well. §9 says a case naming one identifier is
one in which exactly one refusal applies. With no data rows there are no key
values, and `malformed-declaration` is the only refusal left. A table with no
data rows is otherwise accepted (`parse/no-data-rows`).

`parse/key-names-a-stored-column-accepted` has the same header with
`key := id`, which is accepted.
