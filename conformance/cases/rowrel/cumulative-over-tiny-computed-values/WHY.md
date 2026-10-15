# Why this case exists

Ordered by `n`, `a` is 1, 2, 3. `b = a / 100000` is the binary64 quotient
(§4.2 rule 2: "every operator is the corresponding IEEE 754 operation under
round-to-nearest-even"), roughly 1×10^-5, 2×10^-5 and 3×10^-5, and
`e = a * 10000000000000000` is 1×10^16, 2×10^16 and 3×10^16. These are
ordinary binary64 numbers; many hosts print them in exponent form, which
§4.1.6 does not admit as a stored spelling, but a computed value is a number
(§4.2 rule 10: "exactly two kinds of value — a number and an error"), not a
spelling. §2 leaves "number formatting" to the implementation, so how a value
would be printed cannot change what `prior`, `delta` or `cumulative` compute
from it.

§7: `prior(c)` is "that column's value in the preceding row", `delta(c)` is
"`c - prior(c)`", and each `cumulative` value "is one binary64 addition of the
next value to the previous running total". Expected values are binary64 and
written in `expect.json` as the shortest decimal that reads back to them.

This case asserts `cumulative(b)` in the third row: `(b1 + b2) + b3` in
binary64, just above 6×10^-5.
