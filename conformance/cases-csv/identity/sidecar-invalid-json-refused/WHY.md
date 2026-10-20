The sidecar is not valid JSON and the CSV has no other fault (ids unique).
SPEC.md does not define the sidecar's failure modes. Reading: §4 says a
reader that cannot recognise a construct MUST refuse it and MUST NOT
degrade a failed recognition into a different successful one. Ignoring
the sidecar would degrade "key declared" into "no key", which silently
switches off refusal 5, so the file is refused.

## Identifier

This case asserts `refusal: "malformed-declaration"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "the sidecar is this profile's set of declarations, so a sidecar that does not parse, or that declares what cannot be checked, is a malformed declaration, §9.12 `malformed-declaration`:"

§13: "one that is not valid JSON, a leading BOM included"

§9.12: "`malformed-declaration`: a malformed declaration — a line containing `:=` that does not match `declaration`, a `key :=` in function form such as `key := by(id)`, or a `key := col` whose `col` is not a stored column of the table: no column of that name, or a computed one (§4.1.11; see §13 for the CSV profile)"
