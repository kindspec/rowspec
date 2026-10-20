`# note` would be an annotation in .mdtbl. A CSV has no annotation channel
(RFC 4180 defines none, and §9's ignorable channel is "outside the
table" in the .mdtbl sense), so the line is a one-field record against a
two-field header (§9.6). Reading: treating it as a comment would let a CSV
row silently vanish.

## Identifier

This case asserts `refusal: "row-field-count"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a record whose field count differs from the header's, an empty line between rows included, a quoted field the file ends inside, and a stray quote: §9.6 `row-field-count`."

§9.6: "`row-field-count`: a data row whose field count differs from the header"
