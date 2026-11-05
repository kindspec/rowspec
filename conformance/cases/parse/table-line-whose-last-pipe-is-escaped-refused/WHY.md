# Why this case exists

#279. The data row is `| r_1 | x\|`: its last `|` is escaped.

SPEC.md §4.1: `table-line = *WSP "|" 1*( cell "|" ) *WSP eol`,
`cell = *( escaped / ( char - "|" ) )` and `escaped = "\" "|"`, with the
note that `cell` is ambiguous as written and that "The split is NORMATIVELY on
unescaped pipes: `escaped` wins." §4.1.3: "Both the leading and the closing `|`
are required. A cell may contain a pipe **only** as `\|`, and that is the
format's sole escape."

With `escaped` winning, the final `\|` is part of the cell, so the line's
unescaped pipes are the leading one and the one after `r_1`. The cell
` x\|` is never closed: the line lacks its closing `|` and does not match
`table-line`. §4.1.3 says why that is refused rather than read: "The
closing `|` is required rather than optional as in GFM: it is the only
thing that distinguishes a row truncated inside its final cell from a
shorter one, and the field-count refusal (§9.6) cannot see that truncation
because the field count does not change." Read as `r_1` and `x|`, this row
has the header's field count, so nothing else would notice.

§9.18 `malformed-table-line`: "a table line that does not match `table-line`,
in particular one lacking its closing `|` (§4.1.3). **A line is a table line
for this purpose when its first non-`WSP` character is `|`** [...] Such a line
meets both entries, so under §9's note below either identifier is a correct
report". The other entry is §9.19 `unclassified-line`, since the line matches
no alternative of `line`. §9 also says "no conformance case asserts the
narrower one alone", so the case lists both, as
`parse/table-line-missing-closing-pipe` does.

No other entry applies. The table is lines 1 and 2, a valid header and
alignment row; line 3 is not a table line, so it is not "a table line after
the table's contiguous run has ended" either, and `key := id` names the
stored column `id`.

Siblings: `parse/table-line-ending-in-a-backslash-then-an-escaped-pipe-refused`,
`parse/header-line-whose-last-pipe-is-escaped-refused`, and the accepted
control `rowrel/escaped-pipe-before-the-closing-pipe-of-the-last-cell`.
