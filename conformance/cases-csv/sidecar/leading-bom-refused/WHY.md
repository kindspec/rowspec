The sidecar is `{"key": "id"}` preceded by the UTF-8 byte-order mark, EF BB
BF. `id` names a column of the CSV and its values are unique. The CSV has no
BOM.

§13: "One that starts with a BOM is refused too, and that is this profile's
choice: §8.1 says implementations 'MUST NOT add a byte order mark' and that
a parser 'MAY ignore the presence of a byte order mark rather than treating
it as an error', so a reader that ignored one would be conforming JSON.
Refusing it keeps one sidecar readable by every JSON parser, the strict ones
included."

Without the BOM the sidecar is `identity/unique-key-accepted`'s. A reader
whose JSON parser skips a leading BOM accepts this file.

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the sidecar's BOM is the only fault in the file and its
sidecar, so a reader that refuses it has refused for that reason or for one
§13 does not give. What the case does not pin is which reason the reader
reports.
