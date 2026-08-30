# Why this case exists

§7 makes `cumulative` deliberately different from `sum`: "It is a running
total, and each of its values is one binary64 addition of the next value to
the previous running total, taken over the declared order." It is defined as a
sequence of binary64 additions — exactly what `sum` is defined *not* to be.

The three amounts are the same triple whose left-to-right binary64 sum in this
order differs from the correctly-rounded exact sum by one ulp. The last
running total is the stepwise value `1552723.7999999998` — that is,
`(553086.1 + 327400.8) + 672236.9` in binary64 — and **not** `1552723.8`, the
correctly-rounded exact sum of the three. An implementation that "fixes"
`cumulative` to report correctly-rounded exact prefix sums, for symmetry with
§7's rule for `sum`, quietly changes every running total in every ledger; this
case is the tripwire. (`sum` over the same cells is `1552723.8`; the eval pair
under `eval/avg-is-the-exact-mean-not-sum-over-count` uses a triple with the
same property for the aggregate side.)
