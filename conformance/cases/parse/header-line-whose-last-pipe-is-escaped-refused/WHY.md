# Why this case exists

#279 in the header. The file is one line, `| id | a\|`, whose last `|` is
escaped.

SPEC.md §4.1: `table-line = *WSP "|" 1*( cell "|" ) *WSP eol`,
`cell = *( escaped / ( char - "|" ) )` and `escaped = "\" "|"`, with the
note that `cell` is ambiguous as written and that "The split is NORMATIVELY on
unescaped pipes: `escaped` wins." §4.1.3: "Both the leading and the closing `|`
are required. A cell may contain a pipe **only** as `\|`, and that is the
format's sole escape."

As in `parse/table-line-whose-last-pipe-is-escaped-refused`, the final `\|`
is `escaped`, the line has no closing `|`, and it does not match
`table-line`.

§9.18 `malformed-table-line`: "a table line that does not match `table-line`,
in particular one lacking its closing `|` (§4.1.3). **A line is a table line
for this purpose when its first non-`WSP` character is `|`** [...] Such a line
meets both entries, so under §9's note below either identifier is a correct
report". The other entry is §9.19 `unclassified-line`, since the line matches
no alternative of `line`. §9 also says "no conformance case asserts the
narrower one alone", so the case lists both, as
`parse/table-line-missing-closing-pipe` does.

The third identifier: with that line not a `table-line`, the file has
none, and §4.1.2 makes the table "the *maximal contiguous run* of
`table-line`s". So §9.13 `no-table`, "a file containing no table",
applies as well, and §9's note lets a reader report any of the three.

**Why the file is one line.** A header line ending in `\|` cannot be told
apart by acceptance: read the way #279 reports, its last cell unescapes to
`a|`, and §9.16 refuses a column name holding `|` anyway
(`parse/pipe-in-a-column-name-refused`). So the case has to separate the
readings by identifier. A reader that takes the line as a table line sees
a one-line table and reports §9.21 `bad-alignment-row` ("a table shorter
than two lines included") or §9.16 for `a|`. Neither applies here, because
under §4.1 there is no table and no column. Had the file gone on with an
alignment row and data, those lines would form the table under §4.1.2,
with `---` as its column names and `bad-identifier` among its correct
reports, and the case would no longer tell the two readings apart.
