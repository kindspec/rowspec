The sidecar is `{"key": "id"}` encoded as UTF-16 little-endian with its
byte-order mark, FF FE. `id` names a column of the CSV and its values are
unique.

§13: "The sidecar is UTF-8 JSON with no byte-order mark. One that is not
UTF-8 is refused, a sidecar encoded as UTF-16 or UTF-32 included, as RFC
8259 §8.1 requires UTF-8 of JSON exchanged outside a closed ecosystem."

Some JSON readers detect UTF-16 and UTF-32 from the first bytes and decode
them; such a reader accepts this file.

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the sidecar's encoding is the only fault in the file and its
sidecar, so a reader that refuses it has refused for that reason or for one
§13 does not give. What the case does not pin is which reason the reader
reports, or whether a reader calls it an encoding fault, a BOM or invalid
JSON.
