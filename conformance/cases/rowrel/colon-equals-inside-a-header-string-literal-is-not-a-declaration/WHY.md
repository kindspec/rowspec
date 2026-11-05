# Why this case exists

#278 moved to the header. The header line holds `:=` inside a string
literal; the data row does not, so this case fails only for a reader that
mistakes a *header* line for a declaration. A fix for #278 that changes
how data rows are classified, and not how the first table line is, passes
the data-row cases and fails this one.

The line is a table line for the reason the data-row cases give. §4.1:
"**Classification order is normative.** The alternatives of `line` are
tried in the order written and the first that matches decides what the
line is", with `table-line` before `declaration`; `cell` admits `:`, `=`
and `"`. §9.12's "a line containing `:=`" is therefore not reached, which
§9.20 states for header cells in so many words: "§9.12 does not reach it:
that entry is scoped to a line containing `:=`, and a header cell is not
one."

§5: "**The split is at the cell's first `=`.**" The name is `m` and the
formula is `if(a = "x:=y", 1, 2)`; the `=` inside the comparison and the
one inside the string belong to the formula. That is a `cond` whose
`comparison` is `ident "=" string` (§4.2's grammar). §4.2 rule 10: "`=`
and `<>` compare **text or numbers, and the right-hand side's spelling
decides which**. A `string` right-hand side compares text". The row's `a`
is `p`, which is not `x:=y`, so the condition is false and `m` is the
second branch, the literal `2`. The table has one data row, so
`row_index` 0 does not depend on any order.

No case is written for a header *name* holding `:=`, such as `| id | a:=b |`.
That is refused whatever the classification, since §5 splits it into the
name `a:`, which §9.16 refuses, so it cannot tell the two readings apart.
