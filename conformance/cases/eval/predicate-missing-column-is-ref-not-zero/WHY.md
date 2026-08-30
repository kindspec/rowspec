# Why this case exists

§8: "**A name in the predicate that does not resolve is `#REF!(name)`, not a
refusal.** `sum(a where nope = "x")` over a table with no column `nope` is
`#REF!(nope)`, exactly as `sum(nope)` is."

There is no column `kk`, so the predicate can never fire — and a predicate
that can never fire matches no rows, and `sum` over an empty match set is
legitimately `0`. That is the plausible zero §8 says this rule closes:
`#REF!(kk)` is reachable and `0` is not. An implementation that resolves the
predicate lazily, per candidate row, produces the `0` by never noticing the
name at all; this case is the difference between that and treating the
predicate's names as part of the header, resolved before any row is scanned.

`parse/predicate-missing-column-accepted` pins the acceptance half on the same
bytes, and `parse/predicate-computed-twin-of-missing-name-refused` is one
character away (`kk` → `k`, the computed column) and is a §9.22 refusal. The
value asserted here is only meaningful because the file is *not* refused.
