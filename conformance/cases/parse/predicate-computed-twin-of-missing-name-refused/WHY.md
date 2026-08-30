# Why this case exists

§8, distinguishing itself from §9.22: "§9.22 is not a counter-example — it
refuses a *computed* column in a predicate because comparison there is on cell
text and a computed column has none, which is a semantic impossibility rather
than a broken reference."

This file differs from `parse/predicate-missing-column-accepted` by one
character: the predicate names `k`, the computed column, instead of `kk`,
which is absent. Absent is `#REF!(kk)` in an accepted file; computed is a
refusal. The two sit that close and go opposite ways, which is exactly what an
implementation collapses when it handles both as "name isn't a stored column"
— refuse both and it fails the twin, evaluate both and it fails this one.

§9.22 is already pinned by `parse/predicate-lhs-names-a-computed-column-refused`;
this case exists for the *pairing*, so that the boundary between §8's
acceptance and §9.22's refusal is tested from both sides on the same table.
