The first line is `<<<<<<< HEAD`; the next is `id,v`, and both data rows have two fields.

## Identifier

This case asserts `refusal: "conflict-marker"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a conflict marker line, inside a quoted field included: §9.1 `conflict-marker`."

§13: "The header is the first record that does not start on a conflict line, and a file with no such record, such as one holding only `<<<<<<< HEAD`, is §9.1 alone, not also §9.13."

§9.1: "`conflict-marker`: conflict markers on any line — a line whose first seven characters are seven `<`, seven `=`, seven `>`, or seven `|`, the diff3 base marker `|||||||` included (§4.1.12)"
