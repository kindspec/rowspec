The one-byte twin of `markers/leading-marker-line-before-the-header-refused`: the first line is `<<<<<< HEAD`, six `<`, which is data. So it is the header, of one field, and every later row has two.

## Identifier

This case asserts `refusal: "row-field-count"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a record whose field count differs from the header's, an empty line between rows included, a quoted field the file ends inside, and a stray quote: §9.6 `row-field-count`."

§9.6: "`row-field-count`: a data row whose field count differs from the header"

§13: "A shorter run, or one that does not start the line, is data."
