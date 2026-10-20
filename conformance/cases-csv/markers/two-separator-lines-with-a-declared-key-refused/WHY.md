The key is `id`. Two `=======` lines stand among the rows. Were they rows, `id` would hold `=======` twice and the rows would have one field against two.

## Identifier

This case asserts `refusal: "conflict-marker"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a conflict marker line, inside a quoted field included: §9.1 `conflict-marker`."

§13: "A record that starts on one does not count as a row (above), so it is not also §9.6 `row-field-count`, and a file of nothing but conflict lines is not also §9.13 `no-table`."

§13: "But a record that starts on a conflict line is neither the header nor a data row, so no check on rows reaches it, §9.6 included, nor any quoting check, the stray quote and the quoted field the file ends inside above, whatever the header's field count: under the header `id,v`, the line `=======` is a conflict marker, not a data row of one field, and so are `>>>>>>> 5"pipe` and `=======,"x` on the file's last line."

§9.1: "`conflict-marker`: conflict markers on any line — a line whose first seven characters are seven `<`, seven `=`, seven `>`, or seven `|`, the diff3 base marker `|||||||` included (§4.1.12)"

Neither §9.5 nor §9.6 applies: the marker records are not rows, so they hold no key value and have no field count to check.
