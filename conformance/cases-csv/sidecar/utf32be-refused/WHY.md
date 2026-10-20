The sidecar is `{"key": "id"}` encoded as UTF-32 big-endian with no
byte-order mark. `id` names a column of the CSV and its values are unique.

§13: "The sidecar is UTF-8 JSON with no byte-order mark. One that is not
UTF-8 is refused, a sidecar encoded as UTF-16 or UTF-32 included, as RFC
8259 §8.1 requires UTF-8 of JSON exchanged outside a closed ecosystem."

RFC 8259's predecessor let a reader detect UTF-32 from the pattern of zero
bytes, and some readers still do; such a reader accepts this file.

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the sidecar's encoding is the only fault in the file and its
sidecar, so a reader that refuses it has refused for that reason or for one
§13 does not give. What the case does not pin is which reason the reader
reports, or whether a reader calls it an encoding fault or invalid JSON.

## Identifier

This case asserts `refusal: "malformed-declaration"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "the sidecar is this profile's set of declarations, so a sidecar that does not parse, or that declares what cannot be checked, is a malformed declaration, §9.12 `malformed-declaration`:"

§13: "one that is not valid JSON, a leading BOM included"

§13: "A sidecar encoded as UTF-16 or UTF-32 meets whichever rule its bytes meet: with a byte-order mark its bytes are not well-formed UTF-8, so it is `bad-encoding`; without one, a sidecar of ASCII characters only is well-formed UTF-8 that is not valid JSON, so it is `malformed-declaration` as above."

§9.12: "`malformed-declaration`: a malformed declaration — a line containing `:=` that does not match `declaration`, a `key :=` in function form such as `key := by(id)`, or a `key := col` whose `col` is not a stored column of the table: no column of that name, or a computed one (§4.1.11; see §13 for the CSV profile)"

The earlier paragraph on `refusal_contains: ""` describes this case before §13 gave CSV-mode refusals identifiers; it now asserts `malformed-declaration` instead.
