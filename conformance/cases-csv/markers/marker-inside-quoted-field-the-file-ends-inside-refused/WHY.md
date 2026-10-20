Row `r1` opens a quoted value that holds a `>>>>>>> theirs` line, and the file ends before the closing quote.

## Identifier

This case asserts `refusal: ["conflict-marker", "row-field-count"]`: each applies, and reporting any one passes.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a conflict marker line, inside a quoted field included: §9.1 `conflict-marker`."

§13: "a record whose field count differs from the header's, an empty line between rows included, a quoted field the file ends inside, and a stray quote: §9.6 `row-field-count`."

§13: "A file can meet more than one of these, and then each applies, as §9 says: an order column of mixed types under an `order_type`, or under a `columns` type, meets both §9.10 and §9.27, because some of its values are not of the declared type."

§9.1: "`conflict-marker`: conflict markers on any line — a line whose first seven characters are seven `<`, seven `=`, seven `>`, or seven `|`, the diff3 base marker `|||||||` included (§4.1.12)"

§9.6: "`row-field-count`: a data row whose field count differs from the header"

§9: "A conformance case that names one identifier is therefore a case in which exactly one refusal applies; where several apply, the case names each of them, and reporting any one passes."

Under `df99ea1` the conflict line sits inside a quoted field of a record that starts on an ordinary line, so that record is still a data row and every check on rows reaches it. §13: "Records are still split over the whole text, as RFC 4180 splits them, so a conflict line inside a quoted field stays part of that field."
