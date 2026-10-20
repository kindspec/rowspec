`columns` types `n` as `text`; `n` holds `apple` and `2024-01-05`. No key is
declared.

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

`2024-01-05` is not of the declared type: `text` means "a value matching
neither `number` nor `date`", and this is a date. So the file is refused.

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

The earlier paragraph on `refusal_contains: ""` describes this case before §13 gave CSV-mode refusals identifiers; it now asserts `column-type-mismatch` instead.
