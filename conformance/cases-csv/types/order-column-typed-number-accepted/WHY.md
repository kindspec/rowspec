The control for `types/order-column-typed-text-over-numbers-refused`: `o` is
typed `number` and holds `1` and `2`.

§13: "**A blank value is not checked**, so a typed column may hold blanks:
the blank rule above exists because an order needs a place for every row,
and a typed column orders nothing. `columns` does not require `key`. Where
it names the key or the order column, its check applies alongside theirs."

Both the order rules and the type check pass, so the file is accepted.
