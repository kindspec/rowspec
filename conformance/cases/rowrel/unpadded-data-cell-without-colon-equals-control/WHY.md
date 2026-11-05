# Why this case exists

The control for #278's `:=` cases: the same unpadded row, `|r_1|x|`, with
no `:=` in it. #278 reports that this row is accepted where `|r_1|a:=b|` is
refused; this case pins the half that works, so that a failure of the `:=`
cases is read as a failure about `:=` and not about the spacing.

It can fail on its own. `table-line = *WSP "|" 1*( cell "|" ) *WSP eol` puts
no `WSP` between a pipe and a cell's text, and §4.1.4 trims a cell's
leading and trailing `WSP` without requiring any. No other case in the tree
has a data row with no padding at all, so a reader that splits on `" | "`
rather than on `|` is not otherwise caught. The value is `x`, text by
§4.1.6 and §4.1.7.

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
