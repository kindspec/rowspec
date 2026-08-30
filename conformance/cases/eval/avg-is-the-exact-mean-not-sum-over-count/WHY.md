# Why this case exists

§7: "`avg(c)` is the correctly-rounded binary64 value of the exact
mathematical mean", and "`avg` is not `sum` divided by `count`" — this case
separates those two definitions at ordinary magnitudes, with no overflow
anywhere.

The three cells are chosen so that (measured over all six orders) every
binary64 accumulation of the sum agrees with the correctly-rounded exact sum,
`646866.15` — so `s` passes any reasonable summation. The separation is
confined to `avg`: the exact mean is `646866.15.../3`, whose correctly-rounded
binary64 value is `215622.05`, while dividing the *already-rounded* binary64
sum by 3 rounds a second time and lands one ulp away, on
`215622.05000000002`. An implementation computing `avg` as `sum / count`
fails `a` and only `a`. Count is 3 deliberately: division by a power of two is
exact in binary64 and cannot separate the definitions, so a pair or a quartet
of cells could never pin this rule.
