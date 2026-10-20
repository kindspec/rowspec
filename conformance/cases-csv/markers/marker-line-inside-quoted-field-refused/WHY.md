Row `r1` has a quoted value spanning three lines, the middle one `=======`. Every record has two fields.

## Identifier

This case asserts `refusal: "conflict-marker"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a conflict marker line, inside a quoted field included: §9.1 `conflict-marker`."

§9.1: "`conflict-marker`: conflict markers on any line — a line whose first seven characters are seven `<`, seven `=`, seven `>`, or seven `|`, the diff3 base marker `|||||||` included (§4.1.12)"

Under `df99ea1` the conflict line sits inside a quoted field of a record that starts on an ordinary line, so that record is still a data row and every check on rows reaches it. §13: "Records are still split over the whole text, as RFC 4180 splits them, so a conflict line inside a quoted field stays part of that field."
