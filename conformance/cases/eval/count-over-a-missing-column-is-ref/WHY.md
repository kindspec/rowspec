# Why this case exists

The third side of the boundary. §8: "A reference to a name that does not exist
evaluates to `#REF!(name)`."

`count` never coercing a *value* must not be confused with `count` tolerating a
missing *column*. There is no column to count the rows of, so the answer is
`#REF!(nope)` — the failure is in name resolution, before any value is reached.

`eval/missing-agg-col` asserts this for `sum`; nothing asserted it for `count`,
and `count` is the one aggregate whose new rule makes "just return the row
count" a plausible wrong answer here.
