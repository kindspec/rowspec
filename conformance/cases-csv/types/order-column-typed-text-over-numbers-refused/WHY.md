The sidecar declares `key` `id`, `order` `o`, and types `o` as `text`. `o`
holds `1` and `2`.

§13: "**A blank value is not checked**, so a typed column may hold blanks:
the blank rule above exists because an order needs a place for every row,
and a typed column orders nothing. `columns` does not require `key`. Where
it names the key or the order column, its check applies alongside theirs."

§6's order rules accept `o`, a single-type number column, but `columns` says
`text`, and `1` is not text ("`5` in a `text` column is refused"). A reader
that skips `columns` on the order column accepts this file.

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the type mismatch is the only fault in the file and its
sidecar, so a reader that refuses it has refused for that reason or for one
§13 does not give. What the case does not pin is which reason the reader
reports.

## Identifier

This case asserts `refusal: "column-type-mismatch"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a value of a column typed by `columns` that is not of that type, and an order column holding a value that is not of its `order_type`: §9.27 `column-type-mismatch`."

§9.27: "`column-type-mismatch`: a stored value whose type is not the type declared for its column — in §13's CSV profile, by the sidecar's `columns` or its `order_type` (§13)."

The order column has one type, `number`, and no blank or non-finite value, so §9.10 does not apply.

The earlier paragraph on `refusal_contains: ""` describes this case before §13 gave CSV-mode refusals identifiers; it now asserts `column-type-mismatch` instead.
