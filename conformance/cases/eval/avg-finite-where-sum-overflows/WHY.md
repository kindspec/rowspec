# Why this case exists

§7: "`avg(c)` is the correctly-rounded binary64 value of the exact
mathematical mean ... `avg` is not `sum` divided by `count`", and its named
consequence: "`avg` can be finite where `sum` is not."

Four cells of `1e308`. The exact sum is `4e308`, outside binary64 range, so
`sum` is `#REF!(overflow)` under §8's aggregate-overflow paragraph. The exact
mean is `1e308`, an ordinary finite binary64, so `avg` is `1e308`. Both are
asserted in the one case deliberately: an implementation that computes `avg`
as `sum / count` passes `s` and fails `a`, reporting an error for a number it
could have produced — and one that "fixes" that by letting the sum saturate
instead reports a wrong `s`. Only the exact-mean reading passes both.
