# Why this case exists

The header is a single space and a single horizontal tab.

§13: "**A name is trimmed of ASCII space and tab only before §9.2 compares
it** … so are a header cell of spaces, one of a tab and an empty one, so any
two of them are a duplicate." Both trim to the empty name, so the file is
refused (§9.2). No sidecar is supplied and the field counts match, so no
other refusal of §13's profile applies.

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
