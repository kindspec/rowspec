# Why this case exists

The same multiset as `eval/sum-huge-cancellation-positives-first`, under a
declared order that matches its file order. §7's multiset rule makes `sum`
over these four cells `0` — and deliberately excludes `cumulative`, which
remains "one binary64 addition of the next value to the previous running
total" over the declared order. The second step is `1e308 + 1e308`, an
operation whose IEEE result is an infinity, which §4.2 rule 2 makes
`#REF!(overflow)`; §8 adds that no implementation stores an `inf` ("none of
them is ever a number", and §4.1.6 has no spelling for one). The error then
propagates through the remaining steps, so the *last* row's running total is
`#REF!(overflow)`.

The last row, not the second, is asserted deliberately: an implementation that
"fixes" `cumulative` into correctly-rounded exact prefix sums answers `0`
there while still overflowing at row two, so only the final row separates the
stepwise definition from the exact-prefix one.

The unguarded failure mode is not hypothetical: an implementation that lets
the running total accumulate raw doubles returns bare `inf` for this cell — a
raw IEEE infinity escaping the cumulative step unchecked, a value the format
cannot store and §8's four-shapes paragraph says can never be an answer (one
build of the reference did exactly this before the check was added).
