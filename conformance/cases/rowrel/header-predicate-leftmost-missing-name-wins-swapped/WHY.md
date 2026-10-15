# Why this case exists

The twin of `rowrel/header-predicate-leftmost-missing-name-wins` with the
equalities swapped: `t = sum(a where yy = "y" and zz = "x")`. `yy` is now
leftmost, so `t` is `#REF!(yy)`.

§8: "**A name in the predicate that does not resolve is `#REF!(name)`, not a
refusal.**" Both `zz` and `yy` are absent from the header, so two `#REF!`s
apply. §8 decides between them: "Which `#REF!` a formula carries, when more
than one applies, is decided by POSITION IN THE FORMULA TEXT: the leftmost",
and "The leftmost rule reads a declaration's right-hand side the same way ...
Nothing about it is specific to a header cell."

`yy` sorts before `zz`, so a reader that reports the alphabetically first
missing name, or the last one it checked, gives the other answer. The twin
case with the two equalities swapped expects the other name, so no single
fixed choice passes both.
