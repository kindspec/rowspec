# Why this case exists

Ordered by `n`, column `a` holds 9×10^313 (a `9` and 313 zeros), then its
negation, then `1`. The first two match `number` (§4.1.6) and their binary64
values are +infinity and -infinity.

§8: "A **stored** cell whose decimal spelling is finite but whose binary64
value is already infinite is `#REF!(overflow)` wherever it is used as an
operand". §7: each value of `cumulative` "is one binary64 addition of the next
value to the previous running total, taken over the **declared order**", and
"That addition is an operation for the purposes of §4.2 rule 2, so a step
whose result is an infinity is `#REF!(overflow)` and propagates from there".
§7 also says `cumulative` is *not* defined on the exact sum: "only one of
them is defined on the multiset".

So the running total is `#REF!(overflow)` from the first row. The second step
adds an operand that is itself `#REF!(overflow)` to a total that is
`#REF!(overflow)`; both errors are the same value, so which one it carries
does not matter. The third step adds `1` to that error.

The wrong answers this rules out: the host's `inf + -inf`, which is `NaN`
(§4.2 rule 2: "`NaN` cannot arise"); and `0` then `1` from an exact running
sum of the decimal values, which cancel.

This case asserts the second row, where the two infinities meet.
