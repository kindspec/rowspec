`order_type` is `number`, and `o` holds two dates.

§13: "`order_type` declares the order column's type: one of the strings
`number`, `date` or `text`, and anything else, a non-string included, is
refused. Every trimmed value of the order column must then be of that type,
so a column of numbers declared `text` is refused even though it has a
single type."

Neither value is a `number`, so the column is refused.

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

The column has one type, `date`, and no blank or non-finite value, so §9.10 does not apply.

The earlier paragraph on `refusal_contains: ""` describes this case before §13 gave CSV-mode refusals identifiers; it now asserts `column-type-mismatch` instead.
