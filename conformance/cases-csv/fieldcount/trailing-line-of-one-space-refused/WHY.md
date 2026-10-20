The one-byte twin of `fieldcount/single-trailing-empty-line-accepted`: the last line holds one space, so it is a record of one field against a header of two.

## Identifier

This case asserts `refusal: "row-field-count"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "A trailing line that holds only spaces or tabs is not empty, and is a record like any other."

§13: "a record whose field count differs from the header's, an empty line between rows included, a quoted field the file ends inside, and a stray quote: §9.6 `row-field-count`."

§9.6: "`row-field-count`: a data row whose field count differs from the header"
