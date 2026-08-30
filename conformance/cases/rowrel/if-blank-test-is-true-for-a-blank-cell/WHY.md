# Why this case exists

§4.2 rule 10: "**`if(x = "", a, b)` is the blank test**, and it is the one
place in the format where a blank cell is data rather than an absence. A blank
cell's text is the empty string, so the equality is true; it does not become
`#REF!(x)` the way `x + 1` does."

The file is byte-identical to
`rowrel/if-ordering-on-a-blank-is-a-broken-reference` except for the operator,
and the two answers are `1` and `#REF!(q)`. **That is the point.** An
implementation with one blank-handling rule cannot pass both: make blanks loud
everywhere and this case is `#REF!(q)`; make them quiet everywhere and the
sibling is `0`. The format asks for exactly one exception, in exactly one
syntactic position, and the pair is what pins the edge of it.

Rule 10 gives the motive: "without it there is no way to write 'use this when
that is missing', which is the second most common shape in the corpus".

Row `r_01`, which holds `5`, is present so that the assertion is not satisfiable
by an implementation that answers `1` unconditionally; the shape with both rows
totalled is `eval/if-blank-test-guards-the-arithmetic-branch`.
