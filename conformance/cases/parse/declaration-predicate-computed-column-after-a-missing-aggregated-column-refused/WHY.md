# Why this case exists

The declaration `g := sum(nope where b = "2")` aggregates a missing column
under a predicate naming the computed column `b = a * 2`.

§9.22 (`computed-column-compared`): "an equality in a `where` predicate whose
left-hand `ident` ... names a **computed** column (§4.2 rule 5) — in a header
cell and on a declaration line alike". §4.2 rule 5: "The outcome is
**refusal** (§9.22), not a value."

The missing `nope` would make `g` `#REF!(nope)` in an accepted file (§8, §4.2
rule 7), but a value does not suspend a refusal: §9 is a list of things an
implementation "MUST refuse". `b` is `2` in row `r_1` when rendered, which is
the plausible match §4.2 rule 5 exists to forbid. The line matches
`declaration`, so §9.12 does not apply, and nothing else in §9 does.
`eval/declaration-predicate-stored-column-after-a-missing-aggregated-column-is-ref`
is the same file with the predicate naming the stored column `a`.
