The sidecar is `{"key": "caf?"}` where `?` is the single byte E9, which is
`é` in ISO-8859-1 and is not well-formed UTF-8. The CSV's first column is
`café`, in UTF-8, and its values are unique.

§13: "The sidecar is UTF-8 JSON with no byte-order mark. One that is not
UTF-8 is refused, a sidecar encoded as UTF-16 or UTF-32 included, as RFC
8259 §8.1 requires UTF-8 of JSON exchanged outside a closed ecosystem."

A reader that falls back to a legacy encoding when UTF-8 fails reads the key
as `café`, finds the column, and accepts this file.

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the sidecar's encoding is the only fault in the file and its
sidecar, so a reader that refuses it has refused for that reason or for one
§13 does not give. What the case does not pin is which reason the reader
reports.

## Identifier

This case asserts `refusal: "bad-encoding"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a sidecar whose bytes are not well-formed UTF-8: §9.14 `bad-encoding`, which is a property of bytes in whichever file holds them."

§13: "A sidecar encoded as UTF-16 or UTF-32 meets whichever rule its bytes meet: with a byte-order mark its bytes are not well-formed UTF-8, so it is `bad-encoding`; without one, a sidecar of ASCII characters only is well-formed UTF-8 that is not valid JSON, so it is `malformed-declaration` as above."

§9.14: "`bad-encoding`: bytes that are not well-formed UTF-8 (§3). A property of the bytes, decided before any line is classified."

The bytes are not well-formed UTF-8, which §9.14 decides "before any line is classified", so they are never read as JSON and `malformed-declaration` is not also listed; this is the reading §13 gives a UTF-16 sidecar with a byte-order mark, whose bytes likewise "are not well-formed UTF-8, so it is `bad-encoding`".

The earlier paragraph on `refusal_contains: ""` describes this case before §13 gave CSV-mode refusals identifiers; it now asserts `bad-encoding` instead.
