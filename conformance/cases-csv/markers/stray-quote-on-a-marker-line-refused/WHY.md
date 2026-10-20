The line `>>>>>>> 5"pipe` holds a `"` inside a field that does not open with one, which would be a stray quote on a data row.

## Identifier

This case asserts `refusal: "conflict-marker"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a conflict marker line, inside a quoted field included: §9.1 `conflict-marker`."

§13: "But a record that starts on a conflict line is neither the header nor a data row, so no check on rows reaches it, §9.6 included, nor any quoting check, the stray quote and the quoted field the file ends inside above, whatever the header's field count: under the header `id,v`, the line `=======` is a conflict marker, not a data row of one field, and so are `>>>>>>> 5"pipe` and `=======,"x` on the file's last line."

§9.1: "`conflict-marker`: conflict markers on any line — a line whose first seven characters are seven `<`, seven `=`, seven `>`, or seven `|`, the diff3 base marker `|||||||` included (§4.1.12)"
