The sidecar declares `key` `id` and types `id` as `number`. The ids are `1`
and `2`, unique, non-empty, with no whitespace or `Cf`.

§13: "**A blank value is not checked**, so a typed column may hold blanks:
the blank rule above exists because an order needs a place for every row,
and a typed column orders nothing. `columns` does not require `key`. Where
it names the key or the order column, its check applies alongside theirs."

Both checks apply to `id`, and both pass, so the file is accepted.
