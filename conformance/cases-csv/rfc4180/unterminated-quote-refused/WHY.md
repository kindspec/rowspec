The quoted field opened on the second line is never closed, so RFC 4180's
grammar generates no record structure for the rest of the file. SPEC.md
names no CSV-specific refusal for this. Reading: §9 says recognition is
total and §4 says a construct the reader cannot recognise is refused, never
degraded; any lenient recovery invents a field count. Nothing else in the
file is a fault.

## Identifier

This case asserts `refusal: "row-field-count"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a record whose field count differs from the header's, an empty line between rows included, a quoted field the file ends inside, and a stray quote: §9.6 `row-field-count`."

§9.6: "`row-field-count`: a data row whose field count differs from the header"
