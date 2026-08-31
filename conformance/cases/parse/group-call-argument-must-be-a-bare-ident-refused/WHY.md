# Why this case exists

§4.2: `group-call = agg-fn "(" *WSP ident 1*WSP "where" ...` — the aggregated
column is an `ident` with no expression alternative, so `sum((a) where ...)`
is refused (§9.20). Same rule as
`parse/rowrel-call-argument-must-be-a-bare-ident-refused`, on the other call
shape: the two are separate cases because a parser typically has separate
code paths for the two call productions, and admitting an `expr` in either
one creates the nesting site rule 10 says only `cond` has.
