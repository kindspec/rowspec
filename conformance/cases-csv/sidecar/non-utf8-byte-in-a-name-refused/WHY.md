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
