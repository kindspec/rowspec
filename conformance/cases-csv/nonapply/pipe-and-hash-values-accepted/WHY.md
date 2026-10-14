`| a | b` would be refused by §9.18 in .mdtbl (no closing pipe). In a CSV
`|` is not structural, and `#` starts no annotation. Reading: §9.18 and
§9.19 are about .mdtbl line classes a CSV does not have; §13 does not list
them by number, but they concern the pipe table, not the delimiter
file. The header has one column, so every line is a one-field record.
