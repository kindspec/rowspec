Records end in a lone CR, which CSV mode reads as a record break and
warns on (§13). The third record opens a quoted field at its start that
is never closed, so the file ends inside it and is refused (§13,
record boundaries). Issue #94 item 4.

## Identifier

This case asserts `refusal: "row-field-count"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a record whose field count differs from the header's, an empty line between rows included, a quoted field the file ends inside, and a stray quote: §9.6 `row-field-count`."

§13: "A warning, §9.26's and §9.15's included, is not a refusal, and is not checked against the case's identifiers."

§9.6: "`row-field-count`: a data row whose field count differs from the header"
