The sidecar declares `sku`, which is not a column. SPEC.md has no refusal
worded for an undeclared key column. Reading: the .mdtbl analogue for an
order column (§9.10, "not a stored column") is refused, and a key that
names nothing cannot be checked for refusal 5, so accepting it would
degrade a declared key into none (§4). `sku` is itself a valid `ident`, so
§9.16 does not apply.

## Identifier

This case asserts `refusal: "malformed-declaration"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "the sidecar is this profile's set of declarations, so a sidecar that does not parse, or that declares what cannot be checked, is a malformed declaration, §9.12 `malformed-declaration`:"

§13: "a `key` or a `columns` member naming no column of the file. The last is the CSV form of §9.12's `key := col` naming no stored column."

§9.12: "`malformed-declaration`: a malformed declaration — a line containing `:=` that does not match `declaration`, a `key :=` in function form such as `key := by(id)`, or a `key := col` whose `col` is not a stored column of the table: no column of that name, or a computed one (§4.1.11; see §13 for the CSV profile)"
