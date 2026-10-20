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

## Identifier

This case asserts `refusal: "malformed-declaration"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "the sidecar is this profile's set of declarations, so a sidecar that does not parse, or that declares what cannot be checked, is a malformed declaration, §9.12 `malformed-declaration`:"

§13: "one that is not valid JSON, a leading BOM included"

§13: "A sidecar's leading UTF-8 BOM is not §9.26: that entry is a warning in this profile, and the sidecar's BOM is refused, so it is `malformed-declaration` as above."

§9.12: "`malformed-declaration`: a malformed declaration — a line containing `:=` that does not match `declaration`, a `key :=` in function form such as `key := by(id)`, or a `key := col` whose `col` is not a stored column of the table: no column of that name, or a computed one (§4.1.11; see §13 for the CSV profile)"

The earlier paragraph on `refusal_contains: ""` describes this case before §13 gave CSV-mode refusals identifiers; it now asserts `malformed-declaration` instead.
