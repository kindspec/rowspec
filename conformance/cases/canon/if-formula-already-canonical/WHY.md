# Why this case exists

§10's canonical form is "Single-space delimiters, **no alignment padding**", and
that is the whole of it — it is a rule about the *table line*, not about the
text inside a cell. This file is already canonical, so `canon` must return it
byte-for-byte.

The failure this catches is a canonicaliser that reformats the formula: turning
`if(qty > 0, total / qty, 0)` into `if(qty>0,total/qty,0)`, or normalising the
spacing around the commas, or re-emitting the cell from a parsed AST. Any of
those is a change §10 does not authorise, and §10's measured argument is
precisely about *not* touching lines that did not need touching: "two
**genuinely disjoint** edits conflict when padded and merge cleanly when
canonical", and a canonicaliser that rewrites every formula it round-trips
manufactures the same conflicts from the other direction.

`canon(canon(x)) == canon(x)` would still hold for such a reader, which is why
`idempotent` is not enough and this check is `already-canonical`.
