§9.1 refuses a line whose first seven characters are seven `|`. In a CSV
`|` is not structural, so the line is otherwise an ordinary one-field
record matching the one-column header; the marker is the only refusal.

## Identifier

This case asserts `refusal: "conflict-marker"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a conflict marker line, inside a quoted field included: §9.1 `conflict-marker`."

§9.1: "`conflict-marker`: conflict markers on any line — a line whose first seven characters are seven `<`, seven `=`, seven `>`, or seven `|`, the diff3 base marker `|||||||` included (§4.1.12)"

A record that starts on a conflict line does not count as a row, so the marker lines are neither data rows nor key values and §9.6 cannot reach them; §13: "A record that starts on one does not count as a row (above), so it is not also §9.6 `row-field-count`, and a file of nothing but conflict lines is not also §9.13 `no-table`."
