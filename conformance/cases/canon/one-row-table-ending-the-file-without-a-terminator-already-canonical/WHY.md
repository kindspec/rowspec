# Why this case exists

A keyed table of one data row. The `key :=` declaration sits above the table, so the table's last row is the file's last line, and that line has no terminator.

§4.1's production for `file` is `*line`. The grammar puts no order on the kinds of line, and §9's list, which is "complete", has no entry refusing a declaration above the table.

§4.1.1: "`canon` terminates every table line it emits except the file's last line". §10: "The file's final terminator belongs to the file's last line, not to a row: if the file ended with no terminator it still does, after the rows have moved."

The rows are in key order (§6) and the file is in canonical form, so `canon` must return it byte for byte. A `canon` that terminates every table line adds a final `LF` here and fails.
