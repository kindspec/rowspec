# Why this case exists

§4.1.1 and §10: `render(structure(bytes)) == bytes`. Padding, alignment
spellings, the interior whitespace of a formula and the alignment of the
declaration block are all bytes the reader must give back untouched.

An `if` formula is the hardest cell to round-trip because it is the one a reader
is most likely to have parsed into a tree — a comparison, two branches, a
composed unary minus and a multiplication — and re-rendering from that tree
cannot reproduce `if( c>0 , 1 , 0 )`. §4.2's whole-cell recognition rule requires
the parse; §10's byte-exactness requires the original text; a reader has to keep
both.

`y` carries the composition cases (`-if(...) * 10`) into the round-trip so that
a renderer cannot pass by special-casing a bare `if(...)` cell.
