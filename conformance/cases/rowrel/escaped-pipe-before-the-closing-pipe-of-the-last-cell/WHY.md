# Why this case exists

The accepted control for #279. The data row is `| r_1 | x\||`: the last
cell ends in an escaped pipe and is then closed by a real one.

SPEC.md §4.1: `table-line = *WSP "|" 1*( cell "|" ) *WSP eol`,
`cell = *( escaped / ( char - "|" ) )` and `escaped = "\" "|"`, with the
note that `cell` is ambiguous as written and that "The split is NORMATIVELY on
unescaped pipes: `escaped` wins." §4.1.3: "Both the leading and the closing `|`
are required. A cell may contain a pipe **only** as `\|`, and that is the
format's sole escape."

With `escaped` winning, the cells are ` r_1 ` and ` x\|`, and the final
`|` is the closing pipe, so the line matches `table-line` with two fields.
§4.1.3: "A reader splits a **table line** on unescaped pipes and
unescapes `\|` in each cell"; §4.1.4 trims `WSP`. The value is `x|`.

This catches the over-correction of #279: a reader that refuses any line
whose last `|` follows a `\`, rather than one whose last `|` *is* the
escape. `rowrel/escaped-pipe-hugging-the-closing-pipe` pins the same
spelling in a middle cell; this one is in the last cell, where the closing
pipe is also the end of the line.

The table has one data row, so `row_index` 0 does not depend on any order.
