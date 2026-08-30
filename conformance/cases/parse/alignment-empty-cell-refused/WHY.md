# Why this case exists

SPEC.md §4: "The alignment row is required, and its syntax is exactly this:
each cell is one of `---`, `:--`, `--:`, `:-:`, where the run of hyphens is one
or more." An empty cell is none of the four. §4 then states the consequence:
"If the second table line is not a valid alignment row, the file is refused."

`rowspec.table` ACCEPTS an alignment row with an empty cell; `rowspec_alt.table`
refuses it. The reference appears to skip empty cells when checking the row,
which is the same shape of defect as the one that once consumed a data row: a
construct it cannot recognise is degraded into a successful parse rather than
refused.

I judge the reference at fault. The spec enumerates four spellings and an empty
cell is not among them.
