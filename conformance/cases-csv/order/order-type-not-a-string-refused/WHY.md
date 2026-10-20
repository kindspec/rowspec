`order_type` is JSON `null`. `o` holds two numbers.

§13: "`order_type` declares the order column's type: one of the strings
`number`, `date` or `text`, and anything else, a non-string included, is
refused. Every trimmed value of the order column must then be of that type,
so a column of numbers declared `text` is refused even though it has a
single type."

JSON `null` is not one of the three strings, so the sidecar is refused. A
reader that treats a `null` member as absent accepts this file.

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the `order_type` value is the only fault in the file and its
sidecar, so a reader that refuses it has refused for that reason or for one
§13 does not give. What the case does not pin is which reason the reader
reports.

## Identifier

This case asserts `refusal: "malformed-declaration"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "the sidecar is this profile's set of declarations, so a sidecar that does not parse, or that declares what cannot be checked, is a malformed declaration, §9.12 `malformed-declaration`:"

§13: "a `key`, `order`, `order_type` or `delimiter` that is not a string"

§9.12: "`malformed-declaration`: a malformed declaration — a line containing `:=` that does not match `declaration`, a `key :=` in function form such as `key := by(id)`, or a `key := col` whose `col` is not a stored column of the table: no column of that name, or a computed one (§4.1.11; see §13 for the CSV profile)"

The earlier paragraph on `refusal_contains: ""` describes this case before §13 gave CSV-mode refusals identifiers; it now asserts `malformed-declaration` instead.
