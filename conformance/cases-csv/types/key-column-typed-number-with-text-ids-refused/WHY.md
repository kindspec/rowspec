The sidecar declares `key` `id` and types `id` as `number`. The ids are `r1`
and `r2`: valid, unique keys, and text.

§13: "`columns` declares the type of any stored column, the key and order
columns included: a JSON object whose members map a column name to `number`,
`date` or `text`. Any other type, a non-string included, is refused, and so
is a `columns` that is not an object. Two members naming one column, such as
`café` spelt NFC and NFD, are refused as a repeated member is. Each trimmed
value of a named column is classified as an order value is, and refused when
its type is not the declared one: `text` means a value matching neither
`number` nor `date`, so `5` in a `text` column is refused, and `inf`, which
is text by §4.1.6, is refused in a `number` column and admitted in a `text`
one. A number beyond binary64 matches `number` and is admitted: it is
`#REF!(overflow)` where it is used (§8), and nothing here sorts by it."

§13: "**A blank value is not checked**, so a typed column may hold blanks:
the blank rule above exists because an order needs a place for every row,
and a typed column orders nothing. `columns` does not require `key`. Where
it names the key or the order column, its check applies alongside theirs."

The key check passes and the type check does not, so the file is refused. A
reader that skips `columns` on the key column accepts it.

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the type mismatch is the only fault in the file and its
sidecar, so a reader that refuses it has refused for that reason or for one
§13 does not give. What the case does not pin is which reason the reader
reports.
