# Why this case exists

§8: "**The leftmost rule reads a declaration's right-hand side the same
way**, so `g := sum(nope1 where nope2 = "x")` is `#REF!(nope1)`. Nothing
about it is specific to a header cell."

Both names are absent, and they are chosen so the two wrong orderings both
bite: `aa_gone` precedes `zz_gone` alphabetically, so an implementation that
collects misses into a sorted set answers `#REF!(aa_gone)`; and `aa_gone`
sits in the predicate, so an implementation that resolves the predicate
before the aggregated column answers the same. Textually `zz_gone` is
leftmost — it is the aggregate's argument, which in a `group-call` always
precedes the predicate — and that is the assertion.

`eval/leftmost-broken-name-wins` pins the rule for header cells; this case
pins that a declaration line, which reaches the predicate through §4.1's
`rhs` rather than through `formula`, is read by the same rule.
