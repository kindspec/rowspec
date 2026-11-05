# Why this case exists

#278. The data row `| r_1 |a:=b|` holds `:=` inside its `a` cell.

SPEC.md §4.1 decides what a line *is* before anything decides what it means:

> **Classification order is normative.** The alternatives of `line` are tried in
> the order written and the first that matches decides what the line is.

and `line = conflict / annotation / table-line / blank / declaration`, so
`table-line` is tried before `declaration`. The row matches
`table-line = *WSP "|" 1*( cell "|" ) *WSP eol`: `cell = *( escaped / ( char - "|" ) )`
admits `:` and `=`, which are `char`, and admits `WSP` too, so the padding
around each cell, or its absence, is part of the cell. The line is a table line
and `declaration` is never tried. It would not match `declaration` if it were:
that production begins `*WSP ident`, and `ident` (§4.1.9) excludes `|`.

§9.12's "a line containing `:=` that does not match `declaration`" therefore
does not reach the row. §4.1.11 states the same rule with its subject named --
"A declaration is malformed (§9.12) if it contains `:=` and does not match
`declaration`" -- and a table line is not a declaration. SPEC.md gives the
precedent itself for the line kind classified before table lines: §4.1.10 says
`# key := id` "is an annotation, not a malformed declaration", although it too
contains `:=` and does not match `declaration`.

§4.1.4: "A cell's value is its text with leading and trailing `WSP` removed,
and nothing else removed". The value is `a:=b`, which matches neither `number`
(§4.1.6) nor `date` (§4.1.7), so the row's `a` is the text `a:=b`. The table
has one data row, so `row_index` 0 does not depend on any order.

## The edge this pins

The key cell is padded and the `:=` cell is not, so the row ends in
`a:=b|` with no space before the closing pipe.

The spacing variants are siblings, one row each:
`rowrel/colon-equals-in-an-unpadded-data-cell-is-data` (`|r_1|a:=b|`),
`rowrel/colon-equals-in-a-padded-data-cell-is-data` (`| r_1 | a:=b |`),
`rowrel/colon-equals-in-a-data-cell-padded-only-around-itself-is-data`
(`|r_1| a:=b |`),
`rowrel/colon-equals-in-a-data-cell-padded-only-before-the-closing-pipe-is-data`
(`|r_1|a:=b |`) and
`rowrel/colon-equals-in-an-unpadded-cell-after-a-padded-key-is-data`
(`| r_1 |a:=b|`); `rowrel/colon-equals-in-a-data-cell-on-an-indented-line-is-data`
puts `WSP` before the leading `|`. `rowrel/unpadded-data-cell-without-colon-equals-control`
is the same unpadded row with no `:=`, so a reader that fails the unpadded
variant and passes the control is refusing the `:=`, not the spacing.
