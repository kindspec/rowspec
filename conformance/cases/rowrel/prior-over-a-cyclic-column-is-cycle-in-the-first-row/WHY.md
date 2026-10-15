# Why this case exists

`a = b` and `b = a` are a cycle, and `w = prior(a)` reads `a`.

§4.2 rule 9: "**A cycle evaluates to `#REF!(cycle)`**, in every column on the
cycle and in every column whose formula depends, directly or transitively, on
one." `w`'s formula names `a`, so `w` depends on the cycle and is
`#REF!(cycle)`, and §4.2 rule 10's "**Dependency and cycle analysis is over
the whole formula ... and is not affected by which branch a row selects**"
keeps that true in the first row, where `prior` reads no earlier row and
would otherwise be blank. §8: "`#REF!(cycle)` takes precedence ... a cycle is
a property of the whole header".

Ordered by `n`, the rows are `r_1` (`k` = `x`, `v` = 1), `r_2` (`y`, 2) and
`r_3` (`x`, 4). The declared order matches the file order.

This case asserts `w` in the first row.
