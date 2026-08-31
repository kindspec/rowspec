# Why this case exists

§8 notes that `empty`, `overflow` and `cycle` are well-formed `ident`s, so
each collides with a broken reference to a column actually named that — and
accepts the collision deliberately: both readings are errors, both poison
every aggregate identically, and no computed value branches on which one it
is.

This case pins the collision as an equality of values. The table has no
column named `empty`, `overflow` or `cycle`, so `sum(empty)` is a broken
reference carrying the originating name — `#REF!(empty)` — byte-identical to
what `min(opt)` produces for an aggregate with no operands. An implementation
that "helpfully" disambiguates the broken-reference reading (say,
`#REF!(name:empty)`) fails here, which is the point: the collision is
specified, and a sixth shape invented to avoid it is non-conforming.
