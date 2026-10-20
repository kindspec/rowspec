After row `r1` come an empty line and then `>>>>>>> x`, the last line.

## Identifier

This case asserts `refusal: ["conflict-marker", "row-field-count"]`: each applies, and reporting any one passes.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a conflict marker line, inside a quoted field included: §9.1 `conflict-marker`."

§13: "An empty line that only such records follow is not at the end of the file, so it is a data row, and §9.6 refuses it against a header of more than one column."

§13: "a record whose field count differs from the header's, an empty line between rows included, a quoted field the file ends inside, and a stray quote: §9.6 `row-field-count`."

§13: "A file can meet more than one of these, and then each applies, as §9 says: an order column of mixed types under an `order_type`, or under a `columns` type, meets both §9.10 and §9.27, because some of its values are not of the declared type."

§9.1: "`conflict-marker`: conflict markers on any line — a line whose first seven characters are seven `<`, seven `=`, seven `>`, or seven `|`, the diff3 base marker `|||||||` included (§4.1.12)"

§9.6: "`row-field-count`: a data row whose field count differs from the header"

§9: "A conformance case that names one identifier is therefore a case in which exactly one refusal applies; where several apply, the case names each of them, and reporting any one passes."

Without the marker line the empty line would be the single empty line at the end of the file, which is accepted (`fieldcount/single-trailing-empty-line-accepted`); §13: "A single empty line at the end of the file is not between rows and is accepted; a second one is between rows."
