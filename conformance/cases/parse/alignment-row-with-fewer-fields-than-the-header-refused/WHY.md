# Why this case exists

The header has three fields. The alignment row has two, `---` and `--:`,
and each is a valid `align-cell`. The data rows have three.

§9.7, `alignment-field-count`: "an alignment row whose field count differs
from the header". §4: "Its field count must equal the header's."

`parse/align-mismatch` names this identifier only beside
`bad-alignment-row`, so nothing yet tells an implementation that reports
§9.7 from one that always reports §9.21 for a count mismatch.

## Why no other §9 entry applies

- §9.21 `bad-alignment-row`: "a table whose second line is not a valid
  alignment row, a table shorter than two lines included (§4, §4.1.5)".
  §4.1.5 says what validity is: "Every cell of the second table line,
  trimmed, must match `align-cell`", and it is the cell syntax failing that
  sends a file to "§4's rule ... the file is refused rather than
  reinterpreted". Both cells here match. §9.7 itself calls a row like this
  "an alignment row", one whose count is wrong, so a count mismatch is its
  own entry and not a failure to be an alignment row. If §9.21 also covered
  it, §9.7 could never be the only refusal that applies. Where the spec means
  two entries to apply to one line it says so, as §9.18 does for §9.19, and
  §9.7 has no such note.
- §9.6 `row-field-count` is about a **data** row. Both data rows have
  three fields, as the header does.
- §9.8: neither data row is alignment-style; `r_1`, `widget` and `1` are
  not `align-cell`s.
- §9.18, §9.19: every table line has a leading and a closing `|`, the
  table is one contiguous run, and the other lines are a blank and two
  declarations.
- §9.2–§9.5, §9.16: names `id`, `item`, `qty`, `key`, `s` and key values
  `r_1`, `r_2` are distinct `ident`s, and there is one `key` declaration.
- §9.12: both declarations match `declaration`, and `key := id` names a
  stored column. §9.11: `sum` is known.
- §9.1, §9.13, §9.14, §9.15, §9.26: no marker line, a table is present,
  the file is ASCII with LF endings and no BOM.
- §9.9, §9.10, §9.17, §9.20, §9.22–§9.25: no formula, no computed column,
  no `if`, no `order`.
