# Why this case exists

The control for
`parse/declaration-predicate-computed-column-after-a-missing-aggregated-column-refused`:
the predicate names the stored column `a`, so §9.22 does not apply and the
file is accepted.

§4.2 rule 7: "`sum(nope)` is `#REF!(nope)`", and a predicate does not change
that. The predicate `a = "2"` matches row `r_2`, so this is not the empty
match set; the answer is `#REF!(nope)`, not `0`.
