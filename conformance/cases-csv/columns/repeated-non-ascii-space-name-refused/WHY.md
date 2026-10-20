# Why this case exists

Both header names are a single U+3000 IDEOGRAPHIC SPACE.

§13: a leading or trailing non-ASCII space "is part of the name", so each
name is U+3000, and the two are equal, a duplicate (§9.2). Column names are
exempt from §4.1.9's allowlist, so the names themselves are not refused. No
sidecar is supplied and the field counts match, so no other refusal of
§13's profile applies.

The CSV tree asserts only that a file is refused, never which refusal
(§13: "its conformance cases assert only that a file is refused"). This
case is built so that §9.2 is the only refusal SPEC.md gives it, but it
does not prove §9.2 is the one that fired: a reader that refused it for
another reason would pass too.

## Identifier

This case asserts `refusal: "duplicate-column"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "two column names that compare alike, two empty header cells included: §9.2 `duplicate-column`."

§9.2: "`duplicate-column`: a duplicate column name"
