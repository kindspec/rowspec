# Why this case exists

The header cell has padding *outside* the formula, which §10 removes, and
whitespace *inside* the formula, which §4.2 rule 8 makes meaningless but which
§10 gives no licence to touch. `canon(canon(x)) == canon(x)` has to hold across
both.

A canonicaliser that reformats formula interiors is at risk of being
non-idempotent here in a way padding removal never is: the first pass rewrites
`if( c>0 , 1 , 0 )` to some normal form, and if that normal form is then
re-trimmed or re-spaced on the second pass — because the cell's leading spaces
were consumed and the formula's were not, or vice versa — the two outputs
differ.

`canon/if-formula-preserves-values` asserts the other half: whatever `canon`
does to this cell, the numbers must survive it.
