# Why this case exists

SPEC.md §9.1: "conflict markers anywhere in the file -- any line whose first
seven characters are seven `<`, seven `=`, seven `>`, or seven `|`, the diff3
base marker `|||||||` included (§4.1.12)".

§4.1's classification order is what makes this bite: "`conflict` precedes
`table-line` because `|||||||` is *itself* a well-formed seven-cell table line,
so a reader that recognises tables first parses a diff3 conflict as rows of data
and totals them."

The table here has six columns, so `|||||||` -- seven pipes, six empty cells --
matches the field count exactly. Nothing about its shape marks it as wrong; only
the classification order does. A reader that gets the order backwards gains a
blank row and reports a total that is right, from a file that is a
half-finished merge.
