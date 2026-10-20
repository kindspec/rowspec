The sidecar's `columns` is `{"m": "number"}`. The CSV's columns are `id` and
`n`, and `n` holds two numbers.

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

So the sidecar is refused: the CSV has no column `m`, and §13: "A name that
is not a string, or that names no column, is refused, whichever member holds
it".

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the `columns` member is the only fault in the file and its
sidecar, so a reader that refuses it has refused for that reason or for one
§13 does not give. What the case does not pin is which reason the reader
reports.

## Identifier

This case asserts `refusal: "malformed-declaration"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "the sidecar is this profile's set of declarations, so a sidecar that does not parse, or that declares what cannot be checked, is a malformed declaration, §9.12 `malformed-declaration`:"

§13: "a `key` or a `columns` member naming no column of the file. The last is the CSV form of §9.12's `key := col` naming no stored column."

§9.12: "`malformed-declaration`: a malformed declaration — a line containing `:=` that does not match `declaration`, a `key :=` in function form such as `key := by(id)`, or a `key := col` whose `col` is not a stored column of the table: no column of that name, or a computed one (§4.1.11; see §13 for the CSV profile)"

The earlier paragraph on `refusal_contains: ""` describes this case before §13 gave CSV-mode refusals identifiers; it now asserts `malformed-declaration` instead.
