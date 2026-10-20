The sidecar is `{"key": "id"}` in UTF-16 little-endian with no byte-order mark: ASCII characters only, so its bytes are well-formed UTF-8 holding NUL bytes, which is not valid JSON.

## Identifier

This case asserts `refusal: "malformed-declaration"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "the sidecar is this profile's set of declarations, so a sidecar that does not parse, or that declares what cannot be checked, is a malformed declaration, §9.12 `malformed-declaration`:"

§13: "one that is not valid JSON, a leading BOM included"

§13: "A sidecar encoded as UTF-16 or UTF-32 meets whichever rule its bytes meet: with a byte-order mark its bytes are not well-formed UTF-8, so it is `bad-encoding`; without one, a sidecar of ASCII characters only is well-formed UTF-8 that is not valid JSON, so it is `malformed-declaration` as above."

§9.12: "`malformed-declaration`: a malformed declaration — a line containing `:=` that does not match `declaration`, a `key :=` in function form such as `key := by(id)`, or a `key := col` whose `col` is not a stored column of the table: no column of that name, or a computed one (§4.1.11; see §13 for the CSV profile)"
