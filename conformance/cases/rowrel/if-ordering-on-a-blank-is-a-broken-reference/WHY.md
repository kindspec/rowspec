# Why this case exists

§4.2 rule 10: "Every *other* mention of a blank operand stays loud —
`if(x > 0, …)` on a blank `x` is `#REF!(x)`, because that is an ordering
comparison and blank is not a number." And, in the same rule: "an operand that
is not a number — blank, text, or an error — makes the whole `cond` that error,
by §8, exactly as it would in arithmetic."

The wrong answer is `0`, and it is wrong in the way §8 spends its whole section
on: "A broken reference never evaluates to zero, empty, or a stale value. A
blank cell is not zero." An implementation that converts a blank to `0` before
comparing — or that treats a failed conversion as "the comparison is false" —
selects the else branch and produces a number. Every host language's `if` does
one or the other, which is why this is written down.

**Read this case beside `rowrel/if-blank-test-is-true-for-a-blank-cell`.** Same
blank cell, same column, two formulas that differ only in the operator, and the
answers are an error and `1`. That asymmetry is deliberate and is stated as such;
the two cases are siblings and neither is complete without the other.

§8 fixes which name the error carries: "`#REF!(name)` carries the *originating*
name — the column that could not be resolved or whose value would not coerce,
not the column the error surfaces in." So it is `#REF!(q)`, never `#REF!(x)`.
