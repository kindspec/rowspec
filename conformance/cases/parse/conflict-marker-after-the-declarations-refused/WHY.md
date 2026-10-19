# Why this case exists

A valid file with one stray `>>>>>>> theirs` line after its declarations:
a merge resolved by hand where the closing marker was left behind.

§9.1, `conflict-marker`: "conflict markers on any line — a line whose first
seven characters are seven `<`, seven `=`, seven `>`, or seven `|`, the diff3
base marker `|||||||` included (§4.1.12)". §4.1.12: "All four ... are refused
wherever they appear (§9.1) — before any other classification".

Every other case asserting `conflict-marker` also names another identifier,
because its marker sits inside the table and the table lines after it are a
table line after the table (§9.19). Here the marker is the last line of the
file, after the table and the declarations, so it ends no table run and no
table line follows it.

## Why no other §9 entry applies

- §9.19 `unclassified-line` is "a line that is none of annotation, table line,
  declaration, or blank". The marker line is not unmatched: `conflict` is the
  first alternative of `line` in §4.1, and "the first that matches decides
  what the line is". §4.1 sends to §9.19 only "a line matching no
  alternative". Every other line is a table line, the blank line, or a
  declaration.
- §9.12 `malformed-declaration` reaches only "a line containing `:=`". The
  marker line holds none, and both declarations match `declaration`.
- §9.18 `malformed-table-line`: the marker line's first character is `>`,
  not `|`, and the four table lines each have a leading and a closing `|`.
- §9.6, §9.7, §9.8, §9.21: header, alignment row and both data rows have two
  fields; `---` and `--:` are `align-cell`s; no data row is alignment-style.
- §9.2–§9.5, §9.16: names `id`, `q`, `key`, `s` and key values `r_1`, `r_2`
  are distinct `ident`s, and there is one `key` declaration.
- §9.12's `key := col` rule: `id` is a stored column.
- §9.11: `sum` is a known function. §9.13: there is a table. §9.14, §9.15,
  §9.26: the file is ASCII, every line ends in LF, and there is no BOM.
- §9.9, §9.10, §9.17, §9.20, §9.22–§9.25: there is no formula, no computed
  column, no `if` and no `order`.
