# Why this case exists

`key := sum(id)`. §4.1.11: "Read as `key := col`, `key := sum(id)` would
silently key the table on `id`".

§4.1.11: "`key := col` is the sole bare form, because `key` names a column
rather than computing one. **It is also `key`'s only form: `key := fn(col)` is
malformed (§9.12), whatever `fn` is** — `by`, an aggregate function or any
other `ident`, with or without a `where`." §9.12 (`malformed-declaration`)
lists "a `key :=` in function form such as `key := by(id)`".

`id` is a stored column with distinct `ident` values and no `order` is
declared, so nothing else in §9 applies. The same table with `key := id` is
`parse/key-names-a-stored-column-accepted`'s shape, and is accepted.
