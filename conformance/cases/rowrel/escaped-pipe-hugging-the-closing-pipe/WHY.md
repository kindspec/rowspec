# Why this case exists

SPEC.md §4.1.3, as amended: "A cell may contain a pipe **only** as `\|`, and
that is the format's sole escape. A reader splits a table line on unescaped
pipes and unescapes `\|` in each cell; a writer escapes every literal `|` it
emits."

The value is `KS TV | Action` — the real datum from the dogfood run, where
ninety-three television channels in one public registry have a pipe in their own
name and every commit to that file was unrepresentable under the previous rule.

`rowspec_alt` has not been updated for the escape and refuses these files with a
field-count error; per the coordinator that is expected and is not a signal
about the specification.

## The edge this pins

`| r_01 | abc\|| 10 |` has no `WSP` between the escape and the delimiter that
closes the cell. `table-line = *WSP "|" 1*( cell "|" ) *WSP eol` with `\|`
escaped means the cells are `r_01`, `abc\|` and ` 10 `, so the value is `abc|`
and the row has three fields. A reader that scans for `|` before it scans for
`\|` sees four fields and refuses a valid row; one that consumes the escape and
then forgets to expect a delimiter loses the row's last cell.
